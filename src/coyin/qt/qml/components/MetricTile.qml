import QtQuick
import "../support/UiDefaults.js" as UiDefaults
import "../support/MotionCore.js" as MotionCore

Rectangle {
    id: root
    property string label: ""
    property string value: ""
    property string detail: ""
    property string tone: "neutral"
    property var theme: UiDefaults.theme()
    readonly property color baseColor: tone === "accent" ? theme.accentPanel : theme.panelInset

    radius: 6
    color: MotionCore.mixColor(baseColor, theme.accentSurface, tone === "accent" ? 0.06 : 0.02)
    border.color: tone === "accent" ? theme.accentOutline : theme.border
    border.width: 1
    implicitHeight: Math.max(98, tileColumn.implicitHeight + 28)

    Column {
        id: tileColumn
        anchors.fill: parent
        anchors.margins: 14
        spacing: 6

        Rectangle {
            width: 28
            height: 3
            color: tone === "accent" ? theme.anchor : MotionCore.mixColor(theme.borderStrong, theme.anchor, 0.18)
        }

        Text {
            text: root.label
            color: theme.textMuted
            font.pixelSize: 11
        }

        Text {
            text: root.value
            color: tone === "accent" ? theme.anchor : theme.text
            font.pixelSize: 24
            font.weight: Font.DemiBold
        }

        Text {
            text: root.detail
            color: tone === "accent" ? MotionCore.mixColor(theme.textSoft, theme.textMuted, 0.18) : theme.textSoft
            font.pixelSize: 11
            width: parent.width
            wrapMode: Text.Wrap
        }
    }
}
