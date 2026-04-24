#version 440

layout(location = 0) in vec2 vTexCoord;
layout(location = 0) out vec4 fragColor;

layout(std140, binding = 0) uniform buf {
    mat4 qt_Matrix;
    vec4 qt_OpacityAndPadding;
    vec4 sizeRadiusProgressEdge;
    vec4 accentColor;
    vec4 baseColor;
    vec4 options;
} ubuf;

float roundedRectSdf(vec2 point, vec2 halfSize, float radius)
{
    vec2 q = abs(point) - (halfSize - vec2(radius));
    return length(max(q, 0.0)) + min(max(q.x, q.y), 0.0) - radius;
}

float stripe(vec2 uv, float center)
{
    float rel = uv.x - center;
    float leading = smoothstep(-0.10, -0.01, rel);
    float trailing = 1.0 - smoothstep(-0.01, 0.11, rel);
    return max(leading * trailing, 0.0);
}

void main()
{
    vec2 size = ubuf.sizeRadiusProgressEdge.xy;
    float radius = min(ubuf.sizeRadiusProgressEdge.z, min(size.x, size.y) * 0.5);
    vec2 centered = vTexCoord * size - size * 0.5;
    float dist = roundedRectSdf(centered, size * 0.5, radius);
    float aa = max(fwidth(dist), 0.75);
    float inside = 1.0 - smoothstep(0.0, aa, dist);

    float baseAlpha = ubuf.baseColor.a * inside;
    vec3 rgb = ubuf.baseColor.rgb * baseAlpha;
    float alpha = baseAlpha;

    if (ubuf.options.x > 0.5) {
        float phase = ubuf.options.y;
        float glow = 0.0;
        for (int index = 0; index < 5; ++index) {
            float center = phase * 1.3 + (-1.0 + float(index)) * 0.28;
            glow = max(glow, stripe(vTexCoord, center));
        }
        float vertical = 0.72 + 0.28 * (1.0 - abs(vTexCoord.y - 0.5) * 2.0);
        float shineAlpha = glow * vertical * 0.63 * inside * ubuf.accentColor.a;
        rgb += ubuf.accentColor.rgb * shineAlpha;
        alpha = max(alpha, shineAlpha);
    }

    fragColor = vec4(rgb, alpha) * ubuf.qt_OpacityAndPadding.x;
}
