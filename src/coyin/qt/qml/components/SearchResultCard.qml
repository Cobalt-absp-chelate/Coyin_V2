import QtQuick
import QtQuick.Controls
import Coyin.Chrome 1.0
import "."
import "../support/UiDefaults.js" as UiDefaults
import "../support/MotionCore.js" as MotionCore

Rectangle {
    id: root
    property var itemData: ({})
    property var controller: null
    property var theme: UiDefaults.safeTheme(UiDefaults.theme())
    readonly property var motion: MotionCore.tokens(root.theme)

    radius: motion.radiusMedium
    color: root.enabled
           ? MotionCore.mixColor(theme.panelRaised, MotionCore.mixColor(theme.panelHover, theme.accentSurface, 0.22 + interaction.settleStrength * 0.12), interaction.frameStrength)
           : theme.panel
    border.color: root.enabled
                  ? MotionCore.mixColor(theme.border, theme.accentOutline, interaction.frameStrength * 0.76 + interaction.settleStrength * 0.16)
                  : theme.border
    border.width: 1
    implicitHeight: Math.max(infoColumn.implicitHeight, actionColumn.implicitHeight) + 28

    Behavior on color {
        ColorAnimation { duration: MotionCore.duration("panel", root.theme) }
    }

    Behavior on border.color {
        ColorAnimation { duration: MotionCore.duration("panel", root.theme) }
    }

    InteractionTracker {
        id: interaction
        targetItem: root
        cursorEnabled: false
    }

    SignalAccent {
        anchors.fill: parent
        active: interaction.accentStrength > 0.18
        hovered: interaction.hovered
        pressed: interaction.pressed
        accentColor: theme.anchor
        neutralColor: theme.accentSoft
        edge: "frame"
        radius: motion.radiusMedium
    }

    Rectangle {
        anchors.left: parent.left
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        width: 4
        color: MotionCore.mixColor(theme.accentOutline, theme.anchor, interaction.textStrength * 0.36 + interaction.settleStrength * 0.10)

        Behavior on color {
            ColorAnimation { duration: MotionCore.duration("fast", root.theme) }
        }
    }

    Column {
        id: infoColumn
        anchors.left: parent.left
        anchors.leftMargin: 18
        anchors.right: actionColumn.left
        anchors.rightMargin: 16
        anchors.verticalCenter: parent.verticalCenter
        spacing: 10

        Row {
            spacing: 8
            InfoPill { text: itemData.source_label; fillColor: theme.accentSurface; borderColor: theme.accentOutline; textColor: theme.anchor }
            InfoPill { text: itemData.year; fillColor: theme.panelInset; borderColor: theme.border; textColor: theme.textMuted }
            InfoPill { text: itemData.item_type; fillColor: theme.panelInset; borderColor: theme.border; textColor: theme.textMuted }
        }

        Text {
            text: itemData.title
            color: MotionCore.mixColor(theme.text, theme.anchor, interaction.textStrength * 0.26)
            font.pixelSize: 16
            font.weight: Font.DemiBold
            wrapMode: Text.Wrap
            maximumLineCount: 2
            elide: Text.ElideRight
            width: parent.width

            Behavior on color {
                ColorAnimation { duration: MotionCore.duration("fast", root.theme) }
            }
        }

        Text {
            text: itemData.authors
            color: MotionCore.mixColor(theme.textMuted, theme.textSoft, interaction.textStrength * 0.38)
            width: parent.width
            wrapMode: Text.Wrap
            maximumLineCount: 2
            elide: Text.ElideRight

            Behavior on color {
                ColorAnimation { duration: MotionCore.duration("fast", root.theme) }
            }
        }

        Rectangle {
            width: parent.width
            color: MotionCore.mixColor(theme.panelInset, theme.panelFocus, interaction.frameStrength * 0.42 + interaction.settleStrength * 0.06)
            border.color: MotionCore.mixColor(theme.border, theme.accentOutline, interaction.frameStrength * 0.52 + interaction.settleStrength * 0.12)
            border.width: 1
            radius: motion.radiusSmall
            implicitHeight: 64

            Behavior on color {
                ColorAnimation { duration: MotionCore.duration("fast", root.theme) }
            }

            Behavior on border.color {
                ColorAnimation { duration: MotionCore.duration("fast", root.theme) }
            }

            Text {
                anchors.fill: parent
                anchors.margins: 10
                text: itemData.abstract_text
                color: MotionCore.mixColor(theme.textSoft, theme.textMuted, interaction.textStrength * 0.40)
                width: parent.width
                wrapMode: Text.Wrap
                maximumLineCount: 3
                elide: Text.ElideRight

                Behavior on color {
                    ColorAnimation { duration: MotionCore.duration("fast", root.theme) }
                }
            }
        }

        Text {
            visible: !!itemData.meta_summary
            text: itemData.meta_summary
            color: theme.textSoft
            font.pixelSize: 11
            width: parent.width
            elide: Text.ElideRight
        }

        Text {
            text: itemData.status_line
            color: MotionCore.mixColor(theme.textSoft, theme.anchor, interaction.textStrength * 0.66 + interaction.settleStrength * 0.12)
            font.pixelSize: 11
            width: parent.width
            elide: Text.ElideRight

            Behavior on color {
                ColorAnimation { duration: MotionCore.duration("fast", root.theme) }
            }
        }
    }

    Column {
        id: actionColumn
        anchors.right: parent.right
        anchors.rightMargin: 14
        anchors.verticalCenter: parent.verticalCenter
        spacing: 8

        InteractiveButton { theme: root.theme; text: "打开原页"; onClicked: if (controller) controller.openSearchResultLink(itemData.result_id) }
        InteractiveButton { theme: root.theme; text: itemData.has_pdf ? "下载 PDF" : "下载"; onClicked: if (controller) controller.downloadSearchResult(itemData.result_id) }
        InteractiveButton { theme: root.theme; text: "加入资料库"; onClicked: if (controller) controller.addSearchResultToLibrary(itemData.result_id) }
        InteractiveButton { theme: root.theme; text: "入库并分析"; tone: "accent"; onClicked: if (controller) controller.addSearchResultToLibraryAndAnalyze(itemData.result_id) }
    }
}
