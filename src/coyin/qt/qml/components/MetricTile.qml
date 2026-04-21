import QtQuick
import "../support/UiDefaults.js" as UiDefaults

Rectangle {
    id: root
    property string label: ""
    property string value: ""
    property string detail: ""
    property string tone: "neutral"
    property var theme: UiDefaults.theme()

    radius: 6
    color: tone === "accent" ? theme.accentPanel : theme.panelInset
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
            color: tone === "accent" ? theme.anchor : theme.borderStrong
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
            color: theme.textSoft
            font.pixelSize: 11
            width: parent.width
            wrapMode: Text.Wrap
        }
    }
}
