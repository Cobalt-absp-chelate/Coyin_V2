.pragma library

function defaultTokens() {
    return {
        motionProfile: "measured",
        radiusSmall: 4,
        radiusMedium: 6,
        radiusLarge: 8,
        durationImmediate: 126,
        durationFast: 148,
        durationNormal: 182,
        durationSlow: 220,
        durationPanel: 196,
        durationPage: 214,
        hoverShift: -0.42,
        pressShift: 0.52,
        cardHoverShift: -0.72,
        cardPressShift: 0.34,
        pageOffset: 10,
        pageBackdropOffset: 22,
        disabledOpacity: 0.72
    }
}

function tokens(theme) {
    var merged = {}
    var fallback = defaultTokens()
    for (var key in fallback)
        merged[key] = fallback[key]
    if (!theme)
        return merged
    for (var item in fallback) {
        if (theme[item] !== undefined)
            merged[item] = theme[item]
    }
    return merged
}

function duration(name, theme) {
    var t = tokens(theme)
    if (name === "immediate")
        return t.durationImmediate
    if (name === "hover")
        return t.durationFast
    if (name === "focus")
        return t.durationNormal
    if (name === "fast")
        return t.durationFast
    if (name === "slow")
        return t.durationSlow
    if (name === "panel")
        return t.durationPanel
    if (name === "page")
        return t.durationPage
    return t.durationNormal
}

function clamp01(value) {
    return Math.max(0.0, Math.min(1.0, value))
}

function _hexChannel(pair) {
    return parseInt(pair, 16) / 255.0
}

function _expandHex(text) {
    if (text.length === 4 || text.length === 5) {
        var expanded = "#"
        for (var i = 1; i < text.length; ++i)
            expanded += text[i] + text[i]
        return expanded
    }
    return text
}

function toColor(value) {
    if (value === undefined || value === null)
        return Qt.rgba(0, 0, 0, 0)
    if (value.r !== undefined && value.g !== undefined && value.b !== undefined && value.a !== undefined)
        return value

    var text = String(value).trim().toLowerCase()
    if (!text.length || text === "transparent")
        return Qt.rgba(0, 0, 0, 0)

    if (text[0] === "#") {
        var hex = _expandHex(text)
        if (hex.length === 7) {
            return Qt.rgba(
                _hexChannel(hex.slice(1, 3)),
                _hexChannel(hex.slice(3, 5)),
                _hexChannel(hex.slice(5, 7)),
                1.0
            )
        }
        if (hex.length === 9) {
            return Qt.rgba(
                _hexChannel(hex.slice(3, 5)),
                _hexChannel(hex.slice(5, 7)),
                _hexChannel(hex.slice(7, 9)),
                _hexChannel(hex.slice(1, 3))
            )
        }
    }

    return Qt.rgba(0, 0, 0, 0)
}

function mixColor(a, b, t) {
    var mix = clamp01(t)
    var colorA = toColor(a)
    var colorB = toColor(b)
    return Qt.rgba(
        colorA.r + (colorB.r - colorA.r) * mix,
        colorA.g + (colorB.g - colorA.g) * mix,
        colorA.b + (colorB.b - colorA.b) * mix,
        colorA.a + (colorB.a - colorA.a) * mix
    )
}

function weightedShift(hoverProgress, focusProgress, pressProgress, theme, cardLike) {
    var t = tokens(theme)
    var hover = Math.max(hoverProgress || 0, focusProgress || 0)
    var press = pressProgress || 0
    var hoverShift = cardLike ? t.cardHoverShift : t.hoverShift
    var pressShift = cardLike ? t.cardPressShift : t.pressShift
    return hoverShift * hover + pressShift * press
}

function surfaceScale(hoverProgress, focusProgress, pressProgress, settleStrength, cardLike) {
    var hover = Math.max(hoverProgress || 0, focusProgress || 0)
    var press = pressProgress || 0
    var settle = settleStrength || 0
    var hoverLift = cardLike ? 0.010 : 0.007
    var settleLift = cardLike ? 0.004 : 0.002
    var pressDip = cardLike ? 0.014 : 0.010
    return 1.0 + hover * hoverLift + settle * settleLift - press * pressDip
}

function feedbackShade(base, theme, hoverProgress, pressProgress, selectedProgress, focusProgress) {
    var hover = Math.max(hoverProgress || 0, focusProgress || 0)
    var press = pressProgress || 0
    var selected = selectedProgress || 0
    var target = theme && theme.mode === "dark" ? theme.background : theme.textMuted
    var amount = clamp01(hover * 0.045 + press * 0.088 + selected * 0.024)
    return mixColor(base, target, amount)
}

function buttonFill(theme, tone, selected, enabled, hovered, pressed, focused) {
    if (!enabled)
        return theme.panelInset
    var baseColor
    if (tone === "danger") {
        if (pressed)
            baseColor = theme.note
        else if (hovered || focused)
            baseColor = theme.panelAlt
        else
            baseColor = selected ? theme.note : theme.panelRaised
        return feedbackShade(baseColor, theme, hovered ? 1 : 0, pressed ? 1 : 0, selected ? 0.5 : 0, focused ? 1 : 0)
    }
    if (selected)
        baseColor = pressed ? theme.panelFocus : theme.accentPanel
    else if (tone === "accent") {
        if (pressed)
            baseColor = theme.accentPanel
        else if (hovered || focused)
            baseColor = mixColor(theme.panelRaised, theme.accentSurface, 0.70)
        else
            baseColor = theme.panelRaised
    } else if (pressed || focused)
        baseColor = mixColor(theme.panelFocus, theme.accentSurface, 0.22)
    else if (hovered)
        baseColor = mixColor(theme.panelHover, theme.accentSurface, 0.18)
    else
        baseColor = theme.panelRaised
    return feedbackShade(baseColor, theme, hovered ? 1 : 0, pressed ? 1 : 0, selected ? 0.5 : 0, focused ? 1 : 0)
}

function buttonBorder(theme, tone, selected, enabled, hovered, pressed, focused) {
    if (!enabled)
        return theme.border
    if (tone === "danger")
        return hovered || pressed || selected ? theme.danger : theme.border
    if (selected || tone === "accent")
        return theme.accentOutline
    if (pressed || focused)
        return theme.borderStrong
    if (hovered)
        return theme.borderStrong
    return theme.border
}

function buttonText(theme, tone, selected, enabled, hovered, pressed, focused) {
    if (!enabled)
        return theme.textSoft
    if (tone === "danger")
        return hovered || pressed || selected ? theme.danger : theme.text
    if (selected || tone === "accent" || focused)
        return theme.anchor
    if (hovered)
        return theme.text
    return theme.textMuted
}

function chipFill(theme, checked, enabled, hovered, pressed, focused) {
    if (!enabled)
        return theme.panelInset
    var baseColor
    if (checked)
        baseColor = pressed ? theme.accentPanel : theme.accentSurface
    else if (pressed || focused)
        baseColor = mixColor(theme.panelFocus, theme.accentSurface, 0.18)
    else if (hovered)
        baseColor = mixColor(theme.panelHover, theme.accentSurface, 0.14)
    else
        baseColor = theme.panelInset
    return feedbackShade(baseColor, theme, hovered ? 1 : 0, pressed ? 1 : 0, checked ? 0.65 : 0, focused ? 1 : 0)
}

function chipBorder(theme, checked, enabled, hovered, pressed, focused) {
    if (!enabled)
        return theme.border
    if (checked)
        return theme.accentOutline
    if (pressed || focused || hovered)
        return theme.borderStrong
    return theme.border
}

function chipText(theme, checked, enabled, hovered, pressed, focused) {
    if (!enabled)
        return theme.textSoft
    if (checked || focused)
        return theme.anchor
    if (hovered || pressed)
        return theme.text
    return theme.textMuted
}

function tabFill(theme, active, enabled, hovered, pressed, focused) {
    if (!enabled)
        return "transparent"
    var baseColor
    if (active)
        baseColor = pressed ? theme.accentPanel : theme.accentSurface
    else if (pressed || focused)
        baseColor = mixColor(theme.panelFocus, theme.accentSurface, 0.14)
    else if (hovered)
        baseColor = mixColor(theme.panelHover, theme.accentSurface, 0.12)
    else
        baseColor = "transparent"
    return feedbackShade(baseColor, theme, hovered ? 1 : 0, pressed ? 1 : 0, active ? 0.4 : 0, focused ? 1 : 0)
}

function tabBorder(theme, active, enabled, hovered, pressed, focused) {
    if (!enabled)
        return "transparent"
    if (active || focused)
        return theme.accentOutline
    if (pressed || hovered)
        return theme.borderStrong
    return "transparent"
}

function tabText(theme, active, enabled, hovered, pressed, focused) {
    if (!enabled)
        return theme.textSoft
    if (active || focused)
        return theme.anchor
    if (hovered || pressed)
        return theme.text
    return theme.textMuted
}

function cardFill(theme, accentTone, enabled, hovered, pressed, selected) {
    if (!enabled)
        return theme.panel
    var baseColor
    if (selected)
        baseColor = theme.accentPanel
    else if (accentTone)
        baseColor = hovered || pressed ? theme.accentSurface : theme.panelRaised
    else if (pressed)
        baseColor = theme.panelFocus
    else if (hovered)
        baseColor = theme.panelHover
    else
        baseColor = theme.panelRaised
    return feedbackShade(baseColor, theme, hovered ? 1 : 0, pressed ? 1 : 0, selected ? 0.4 : 0, 0)
}

function cardBorder(theme, accentTone, enabled, hovered, pressed, selected) {
    if (!enabled)
        return theme.border
    if (selected || accentTone)
        return hovered || pressed || selected ? theme.accentOutline : theme.border
    if (hovered || pressed)
        return theme.borderStrong
    return theme.border
}

function panelFill(theme, enabled, hovered, pressed, selected) {
    if (!enabled)
        return theme.panel
    var baseColor
    if (selected)
        baseColor = theme.accentPanel
    else if (pressed)
        baseColor = theme.panelFocus
    else if (hovered)
        baseColor = theme.panelHover
    else
        baseColor = theme.panelInset
    return feedbackShade(baseColor, theme, hovered ? 1 : 0, pressed ? 1 : 0, selected ? 0.45 : 0, 0)
}

function panelBorder(theme, enabled, hovered, pressed, selected) {
    if (!enabled)
        return theme.border
    if (selected)
        return theme.accentOutline
    if (hovered || pressed)
        return theme.borderStrong
    return theme.border
}
