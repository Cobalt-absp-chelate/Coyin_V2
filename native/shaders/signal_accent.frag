#version 440

layout(location = 0) in vec2 vTexCoord;
layout(location = 0) out vec4 fragColor;

layout(std140, binding = 0) uniform buf {
    mat4 qt_Matrix;
    vec4 qt_OpacityAndPadding;
    vec4 sizeRadiusProgressEdge;
    vec4 accentColor;
    vec4 neutralColor;
    vec4 options;
} ubuf;

float roundedRectSdf(vec2 point, vec2 halfSize, float radius)
{
    vec2 q = abs(point) - (halfSize - vec2(radius));
    return length(max(q, 0.0)) + min(max(q.x, q.y), 0.0) - radius;
}

float edgeStrength(float edgeType, vec2 uv)
{
    if (edgeType < 0.5) {
        return 1.0 - smoothstep(0.0, 0.38, uv.x);
    }
    if (edgeType < 1.5) {
        return smoothstep(0.62, 1.0, uv.x);
    }
    if (edgeType < 2.5) {
        return smoothstep(0.65, 1.0, uv.y);
    }
    if (edgeType < 3.5) {
        return 1.0 - smoothstep(0.0, 0.35, uv.y);
    }

    float borderDistance = min(min(uv.x, 1.0 - uv.x), min(uv.y, 1.0 - uv.y));
    float frame = 1.0 - smoothstep(0.0, 0.18, borderDistance);
    float diagonal = 1.0 - smoothstep(0.0, 0.9, abs(uv.x - uv.y));
    return frame * (0.72 + 0.28 * diagonal);
}

void main()
{
    float progress = ubuf.sizeRadiusProgressEdge.w;
    if (progress <= 0.0001) {
        discard;
    }

    vec2 size = ubuf.sizeRadiusProgressEdge.xy;
    float radius = min(ubuf.sizeRadiusProgressEdge.z, min(size.x, size.y) * 0.5);
    vec2 centered = vTexCoord * size - size * 0.5;
    float dist = roundedRectSdf(centered, size * 0.5, radius);
    float aa = max(fwidth(dist), 0.75);
    float inside = 1.0 - smoothstep(0.0, aa, dist);
    float border = 1.0 - smoothstep(0.35, 1.45 + aa, abs(dist));
    float edge = edgeStrength(ubuf.options.x, vTexCoord) * inside;

    float fillAlpha = (0.12 + progress * 0.18) * inside * ubuf.neutralColor.a;
    float borderAlpha = (0.10 + progress * 0.28) * border * ubuf.accentColor.a;
    float glowAlpha = (0.16 + progress * 0.48) * edge * ubuf.accentColor.a;

    vec3 rgb = ubuf.neutralColor.rgb * fillAlpha
             + ubuf.accentColor.rgb * (borderAlpha + glowAlpha);
    float alpha = clamp(fillAlpha + borderAlpha + glowAlpha, 0.0, 1.0);

    fragColor = vec4(rgb, alpha) * ubuf.qt_OpacityAndPadding.x;
}
