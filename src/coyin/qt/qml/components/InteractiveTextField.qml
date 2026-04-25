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

    InteractionTracker {
        id: interaction
        targetItem: root
        cursorShape: Qt.IBeamCursor
        busy: root.busy
        selected: root.selected
        focusedInput: root.activeFocus
    }

    background: Rectangle {
        radius: MotionCore.tokens(root.theme).radiusSmall
        color: MotionCore.mixColor(
            root.enabled ? root.theme.panelInset : root.theme.panel,
            root.theme.panelFocus,
            interaction.focusProgress * 0.28 + interaction.hoverProgress * 0.10 + interaction.selectionProgress * 0.18
        )
        border.color: MotionCore.mixColor(
            root.theme.border,
            root.theme.accentOutline,
            interaction.frameStrength * 0.52 + interaction.settleStrength * 0.24
        )
        border.width: 1
        opacity: root.enabled ? 1.0 : 0.74

        Behavior on color {
            ColorAnimation { duration: MotionCore.duration("fast", root.theme) }
        }

        Behavior on border.color {
            ColorAnimation { duration: MotionCore.duration("fast", root.theme) }
        }

        Behavior on opacity {
            NumberAnimation { duration: MotionCore.duration("immediate", root.theme) }
        }

        SignalAccent {
            anchors.fill: parent
            active: interaction.active
            hovered: interaction.hovered
            pressed: false
            accentColor: root.theme.anchor
            neutralColor: root.theme.accentSoft
            edge: "bottom"
            radius: MotionCore.tokens(root.theme).radiusSmall
        }

    }
}
