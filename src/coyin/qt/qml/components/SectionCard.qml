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
    border.color: root.interactive && interaction.hovered ? root.accentColor : borderColor
    border.width: 1
    implicitHeight: headerColumn.implicitHeight + content.implicitHeight + 44

    Behavior on border.color {
        ColorAnimation { duration: 110 }
    }

    default property alias cardContent: content.data

    InteractionState {
        id: interaction
        enabledInput: root.enabled
        visibleInput: root.visible
        hoveredInput: hoverHandler.hovered
        pressedInput: false
        focusedInput: false
        busyInput: false
        selectedInput: false
    }

    SignalAccent {
        anchors.fill: parent
        visible: root.interactive
        active: interaction.active
        hovered: interaction.hovered
        pressed: interaction.pressed
        accentColor: root.accentColor
        neutralColor: root.accentSoft
        edge: "frame"
        radius: root.radius
    }

    HoverHandler {
        id: hoverHandler
        enabled: root.interactive && root.visible
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
                color: root.interactive && interaction.hovered ? root.textColor : root.accentColor

                Behavior on color {
                    ColorAnimation { duration: 110 }
                }
            }

            Text {
                id: titleLabel
                font.family: "Microsoft YaHei UI"
                font.pixelSize: 16
                font.weight: Font.DemiBold
                color: root.textColor

                Behavior on color {
                    ColorAnimation { duration: 110 }
                }
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
