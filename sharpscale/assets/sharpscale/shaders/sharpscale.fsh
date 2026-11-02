#version 330 core

// SharpScale: smooth upscale of the render-scaled scene plus contrast-adaptive sharpening.
// Sampler is LINEAR (bound by the mod), so each tap is a bilinear sample of the low-res scene.
// Sharpening follows AMD CAS (MIT): per-pixel weight from local min/max, no ringing on edges.

uniform sampler2D scene;
uniform vec2 srcTexel;   // 1 / source (scaled) size
uniform float sharpness; // 0 = off, 1 = max
uniform int mode;        // 0 = bilinear only, 1 = bilinear + CAS

in vec2 texCoord;

out vec4 outColor;

void main(void)
{
	vec3 c = texture(scene, texCoord).rgb;
	if (mode == 0 || sharpness <= 0.0) {
		outColor = vec4(c, 1.0);
		return;
	}

	vec3 n = texture(scene, texCoord + vec2(0.0, srcTexel.y)).rgb;
	vec3 s = texture(scene, texCoord - vec2(0.0, srcTexel.y)).rgb;
	vec3 e = texture(scene, texCoord + vec2(srcTexel.x, 0.0)).rgb;
	vec3 w = texture(scene, texCoord - vec2(srcTexel.x, 0.0)).rgb;

	vec3 mn = min(c, min(min(n, s), min(e, w)));
	vec3 mx = max(c, max(max(n, s), max(e, w)));

	vec3 amp = sqrt(clamp(min(mn, 1.0 - mx) / max(mx, vec3(1e-5)), 0.0, 1.0));
	float peak = -1.0 / mix(8.0, 5.0, clamp(sharpness, 0.0, 1.0));
	vec3 wgt = amp * peak;

	vec3 o = (c + wgt * (n + s + e + w)) / (1.0 + 4.0 * wgt);
	outColor = vec4(clamp(o, 0.0, 1.0), 1.0);
}
