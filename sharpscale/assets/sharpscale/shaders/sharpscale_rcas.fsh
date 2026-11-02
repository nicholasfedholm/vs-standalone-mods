#version 330 core

// SharpScale 0.2.0 - FSR 1 RCAS (Robust Contrast Adaptive Sharpening), pass B.
// Port of AMD FidelityFX Super Resolution 1.0 FsrRcasF (ffx_fsr1.h) to GLSL 330,
// with the optional noise detection (FSR_RCAS_DENOISE) enabled.
// Differences from the reference: texelFetch with clamped texel offsets; exact reciprocals
// (guarded against divide-by-zero) replace the APrx* approximations.
//
// Copyright (c) 2021 Advanced Micro Devices, Inc. All rights reserved.
// Permission is hereby granted, free of charge, to any person obtaining a copy of this
// software and associated documentation files (the "Software"), to deal in the Software
// without restriction, including without limitation the rights to use, copy, modify, merge,
// publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons
// to whom the Software is furnished to do so, subject to the following conditions:
// The above copyright notice and this permission notice shall be included in all copies or
// substantial portions of the Software.
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
// INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR
// PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE
// FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
// OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
// DEALINGS IN THE SOFTWARE.
//
// Input is the full-resolution EASU output (same colour space as the scene texture).
// Viewport must start at (0,0); one input texel per output pixel.

uniform sampler2D scene;
uniform float rcasCon; // exp2(-RcasStops); 1.0 = sharpest

out vec4 outColor;

#define FSR_RCAS_LIMIT (0.25 - (1.0 / 16.0))

float lumaOf(vec3 c)
{
	return c.b * 0.5 + (c.r * 0.5 + c.g);
}

void main(void)
{
	ivec2 sz = textureSize(scene, 0);
	ivec2 sp = ivec2(gl_FragCoord.xy);
	ivec2 hi = sz - ivec2(1);

	//    b
	//  d e f
	//    h
	vec3 b = texelFetch(scene, clamp(sp + ivec2( 0, -1), ivec2(0), hi), 0).rgb;
	vec3 d = texelFetch(scene, clamp(sp + ivec2(-1,  0), ivec2(0), hi), 0).rgb;
	vec3 e = texelFetch(scene, clamp(sp,                 ivec2(0), hi), 0).rgb;
	vec3 f = texelFetch(scene, clamp(sp + ivec2( 1,  0), ivec2(0), hi), 0).rgb;
	vec3 h = texelFetch(scene, clamp(sp + ivec2( 0,  1), ivec2(0), hi), 0).rgb;

	float bL = lumaOf(b), dL = lumaOf(d), eL = lumaOf(e), fL = lumaOf(f), hL = lumaOf(h);

	// Noise detection.
	float nz = 0.25 * bL + 0.25 * dL + 0.25 * fL + 0.25 * hL - eL;
	float lumRange = max(max(max(bL, dL), max(eL, fL)), hL) - min(min(min(bL, dL), min(eL, fL)), hL);
	nz = clamp(abs(nz) / max(lumRange, 1.0e-6), 0.0, 1.0);
	nz = -0.5 * nz + 1.0;

	// Min and max of the ring (b, d, f, h).
	vec3 mn4 = min(min(b, d), min(f, h));
	vec3 mx4 = max(max(b, d), max(f, h));

	// Limiters (guarded high precision reciprocals).
	vec3 hitMin = min(mn4, e) / max(4.0 * mx4, vec3(1.0e-6));
	vec3 hitMax = (1.0 - max(mx4, e)) / min(4.0 * mn4 - 4.0, vec3(-1.0e-6));
	vec3 lobeRGB = max(-hitMin, hitMax);
	float lobe = max(-FSR_RCAS_LIMIT, min(max(lobeRGB.r, max(lobeRGB.g, lobeRGB.b)), 0.0)) * rcasCon;

	// Noise removal.
	lobe *= nz;

	// Resolve.
	float rcpL = 1.0 / (4.0 * lobe + 1.0);
	vec3 pix = (lobe * b + lobe * d + lobe * h + lobe * f + e) * rcpL;
	outColor = vec4(clamp(pix, 0.0, 1.0), 1.0);
}
