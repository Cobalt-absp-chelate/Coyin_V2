import QtQuick
import QtQuick.Controls
import Coyin.Chrome 1.0
import "../support/UiDefaults.js" as UiDefaults
import "../support/MotionCore.js" as MotionCore

TextField {
    id: root
    property var theme: UiDefaults.safeTheme(UiDefaults.theme())
    property bool busy: false
    property bool selected: false

    padding: 10
    color: theme.text
    font.family: "Microsoft YaHei UI"
    font.pixelSize: 12
    selectByMouse: true

    InteractionState {
        id: interaction
        enabledInput: root.enabled
        visibleInput: root.visible
        hoveredInput: hoverHandler.hovered
        pressedInput: false
        focusedInput: root.activeFocus
        busyInput: root.busy
        selectedInput: root.selected
    }

    background: Rectangle {
        radius: MotionCore.tokens().radiusSmall
        color: root.enabled ? root.theme.panelInset : root.theme.panel
        border.color: root.activeFocus || root.selected ? root.theme.accentOutline : root.theme.border
        border.width: 1
        opacity: root.enabled ? 1.0 : 0.74

        SignalAccent {
            anchors.fill: parent
            active: interaction.active
            hovered: interaction.hovered
            pressed: false
            accentColor: root.theme.anchor
            neutralColor: root.theme.accentSoft
            edge: "bottom"
            radius: MotionCore.tokens().radiusSmall
        }

        HoverHandler {
            id: hoverHandler
            enabled: root.enabled && root.visible
        }
    }
}
