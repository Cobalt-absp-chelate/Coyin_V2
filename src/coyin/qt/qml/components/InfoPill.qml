import QtQuick
import "../support/UiDefaults.js" as UiDefaults

Rectangle {
    id: root
    property alias text: label.text
    property color fillColor: UiDefaults.theme().panelInset
    property color borderColor: UiDefaults.theme().border
    property color textColor: UiDefaults.theme().textMuted

    radius: 3
    color: fillColor
    border.color: borderColor
    border.width: 1
    implicitHeight: 24
    implicitWidth: label.implicitWidth + 16

    Text {
        id: label
        anchors.centerIn: parent
        color: root.textColor
        font.family: "Microsoft YaHei UI"
        font.pixelSize: 11
    }
}
