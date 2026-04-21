import QtQuick
import QtQuick.Controls
import Coyin.Chrome 1.0
import "../support/UiDefaults.js" as UiDefaults

Rectangle {
    id: root
    property alias title: titleLabel.text
    property alias caption: captionLabel.text
    property color panelColor: UiDefaults.theme().panelRaised
    property color borderColor: UiDefaults.theme().border
    property color textColor: UiDefaults.theme().text
    property color captionColor: UiDefaults.theme().textSoft
    property color accentColor: UiDefaults.theme().anchor
    property color accentSoft: UiDefaults.theme().accentSoft
    property bool interactive: false

    radius: 6
    color: panelColor
    border.color: borderColor
    border.width: 1
    implicitHeight: headerColumn.implicitHeight + content.implicitHeight + 44

    default property alias cardContent: content.data

    SignalAccent {
        anchors.fill: parent
        visible: root.interactive
        active: false
        hovered: hover.containsMouse
        pressed: false
        accentColor: root.accentColor
        neutralColor: root.accentSoft
        edge: "frame"
        radius: root.radius
    }

    MouseArea {
        id: hover
        anchors.fill: parent
        hoverEnabled: true
        acceptedButtons: Qt.NoButton
        visible: root.interactive
    }

    Column {
        anchors.fill: parent
        anchors.margins: 16
        spacing: 12

        Column {
            id: headerColumn
            width: parent.width
            spacing: 6

            Rectangle {
                width: 30
                height: 3
                color: root.accentColor
            }

            Text {
                id: titleLabel
                font.family: "Microsoft YaHei UI"
                font.pixelSize: 16
                font.weight: Font.DemiBold
                color: root.textColor
            }

            Text {
                id: captionLabel
                visible: text.length > 0
                width: parent.width
                color: root.captionColor
                font.pixelSize: 11
                wrapMode: Text.Wrap
            }
        }

        Column {
            id: content
            width: parent.width
            spacing: 10
        }
    }
}
