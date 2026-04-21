import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Coyin.Chrome 1.0
import "../support/UiDefaults.js" as UiDefaults
import "../support/MotionCore.js" as MotionCore

Item {
    id: root
    property var theme: UiDefaults.safeTheme(UiDefaults.theme())
    property string title: ""
    property string subtitle: ""
    property bool expanded: false
    signal toggled(bool expanded)

    default property alias sectionContent: bodyColumn.data
    implicitHeight: container.implicitHeight

    Rectangle {
        id: container
        anchors.left: parent.left
        anchors.right: parent.right
        implicitHeight: header.implicitHeight + bodyWrapper.height + 12
        radius: MotionCore.tokens().radiusMedium
        color: root.theme.panelRaised
        border.color: root.expanded ? root.theme.accentOutline : root.theme.border
        border.width: 1

        Column {
            anchors.fill: parent
            anchors.margins: 6
            spacing: 6

            Rectangle {
                id: header
                width: parent.width
                implicitHeight: 54
                radius: MotionCore.tokens().radiusSmall
                color: root.expanded ? root.theme.accentPanel : root.theme.panelInset
                border.color: root.expanded ? root.theme.accentOutline : root.theme.border
                border.width: 1

                SignalAccent {
                    anchors.fill: parent
                    active: root.expanded || expanderMouse.pressed
                    hovered: expanderMouse.containsMouse
                    pressed: expanderMouse.pressed
                    accentColor: root.theme.anchor
                    neutralColor: root.theme.accentSoft
                    edge: "frame"
                    radius: MotionCore.tokens().radiusSmall
                }

                RowLayout {
                    anchors.fill: parent
                    anchors.margins: 12
                    spacing: 12

                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 3

                        Text {
                            id: titleLabel
                            text: root.title
                            color: root.expanded ? root.theme.anchor : root.theme.text
                            font.family: "Microsoft YaHei UI"
                            font.pixelSize: 14
                            font.weight: Font.DemiBold
                        }

                        Text {
                            visible: root.subtitle.length > 0
                            text: root.subtitle
                            color: root.theme.textSoft
                            font.pixelSize: 11
                            wrapMode: Text.Wrap
                        }
                    }

                    Text {
                        text: root.expanded ? "收起" : "展开"
                        color: root.expanded ? root.theme.anchor : root.theme.textMuted
                        font.pixelSize: 11
                        font.weight: Font.Medium
                    }
                }

                MouseArea {
                    id: expanderMouse
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: {
                        root.expanded = !root.expanded
                        root.toggled(root.expanded)
                    }
                }
            }

            Item {
                id: bodyWrapper
                width: parent.width
                clip: true
                height: root.expanded ? bodyColumn.implicitHeight + 12 : 0
                visible: height > 0

                Behavior on height {
                    NumberAnimation {
                        duration: MotionCore.duration("normal")
                    }
                }

                Column {
                    id: bodyColumn
                    width: parent.width
                    anchors.top: parent.top
                    anchors.topMargin: 6
                    spacing: 10
                }
            }
        }
    }
}
