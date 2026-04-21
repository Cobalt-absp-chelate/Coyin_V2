.pragma library

function tokens() {
    return {
        radiusSmall: 4,
        radiusMedium: 6,
        radiusLarge: 8,
        durationFast: 110,
        durationNormal: 170,
        durationSlow: 220
    }
}

function duration(name) {
    var t = tokens()
    if (name === "fast")
        return t.durationFast
    if (name === "slow")
        return t.durationSlow
    return t.durationNormal
}

function buttonFill(theme, tone, selected, enabled) {
    if (!enabled)
        return theme.panelInset
    if (selected || tone === "accent")
        return theme.accentPanel
    if (tone === "danger")
        return theme.note
    return theme.panelRaised
}

function buttonBorder(theme, tone, selected, enabled) {
    if (!enabled)
        return theme.border
    if (selected || tone === "accent")
        return theme.accentOutline
    if (tone === "danger")
        return theme.danger
    return theme.border
}

function buttonText(theme, tone, selected, enabled) {
    if (!enabled)
        return theme.textSoft
    if (selected || tone === "accent")
        return theme.anchor
    if (tone === "danger")
        return theme.danger
    return theme.text
}
