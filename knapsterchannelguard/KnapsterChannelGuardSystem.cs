using System;
using System.Collections;
using System.Linq;
using HarmonyLib;
using Vintagestory.API.Common;
using Vintagestory.API.Server;

namespace KnapsterChannelGuard;

// KnapsterAdminModMenu.StartServerSide can throw before it registers ModMenuSettingsPacket.
// The client always registers it, so every id on the "knapster" channel is then off by one
// and the client crashes decoding the next settings packet (ProtoException on world join).
public class KnapsterChannelGuardSystem : ModSystem
{
    const string HarmonyId = "knapsterchannelguard";
    const string MenuType = "Knapster.Features.ModMenu.Systems.KnapsterAdminModMenu";
    const string PacketType = "Knapster.Features.ModMenu.Systems.ModMenuSettingsPacket";
    const string ChannelName = "knapster";

    static ICoreServerAPI sapi;
    Harmony harmony;

    public override double ExecuteOrder() => 999;
    public override bool ShouldLoad(EnumAppSide side) => side == EnumAppSide.Server;

    public override void StartPre(ICoreAPI api)
    {
        sapi = api as ICoreServerAPI;
        var menu = FindType(MenuType);
        if (menu == null)
        {
            api.Logger.Notification("[KnapsterChannelGuard] Knapster not loaded, nothing to guard.");
            return;
        }

        var target = AccessTools.Method(menu, "StartServerSide", new[] { typeof(ICoreServerAPI) });
        harmony = new Harmony(HarmonyId);
        var prefix = Environment.GetEnvironmentVariable("KNAPSTERCHANNELGUARD_FORCE") == "1"
            ? new HarmonyMethod(typeof(KnapsterChannelGuardSystem), nameof(ForceFailure))
            : null;
        harmony.Patch(target, prefix: prefix, finalizer: new HarmonyMethod(typeof(KnapsterChannelGuardSystem), nameof(Finalizer)));
    }

    public override void StartServerSide(ICoreServerAPI api)
    {
        var channel = api.Network.GetChannel(ChannelName);
        if (channel == null) return;
        var types = MessageTypes(channel);
        var map = types.Keys.Cast<Type>().OrderBy(t => (int)types[t]).Select(t => $"{types[t]}={t.FullName}");
        api.Logger.Notification("[KnapsterChannelGuard] channel map: " + string.Join(";", map));
    }

    public override void Dispose()
    {
        harmony?.UnpatchAll(HarmonyId);
        sapi = null;
    }

    static void ForceFailure() => throw new NullReferenceException("forced by KNAPSTERCHANNELGUARD_FORCE");

    static Exception Finalizer(Exception __exception)
    {
        if (__exception == null) return null;

        sapi.Logger.Warning("[KnapsterChannelGuard] Knapster admin menu failed to start: {0}", __exception.Message);
        var packet = FindType(PacketType);
        var channel = sapi.Network.GetChannel(ChannelName) ?? sapi.Network.RegisterChannel(ChannelName);
        if (!MessageTypes(channel).Contains(packet))
        {
            channel.RegisterMessageType(packet);
            sapi.Logger.Warning("[KnapsterChannelGuard] Registered {0} so ids match the client. The /knapster gui command is unavailable this session.", packet.Name);
        }
        return null;
    }

    static IDictionary MessageTypes(IServerNetworkChannel channel) =>
        (IDictionary)AccessTools.Field(channel.GetType(), "messageTypes").GetValue(channel);

    static Type FindType(string name) =>
        AppDomain.CurrentDomain.GetAssemblies()
            .Where(a => a.GetName().Name == "Knapster")
            .Select(a => a.GetType(name))
            .FirstOrDefault(t => t != null);
}
