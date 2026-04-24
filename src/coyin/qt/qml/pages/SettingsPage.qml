import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Coyin.Chrome 1.0
import "../components"
import "../support/UiDefaults.js" as UiDefaults
import "../support/MotionCore.js" as MotionCore

Item {
    id: root
    objectName: "settingsPage"
    property var controller: null
    property var theme: UiDefaults.safeTheme(UiDefaults.theme())
    property string currentCategory: "appearance"
    property bool suppressSync: false

    readonly property var providerEntries: controller ? controller.providerEntries : []
    readonly property var pluginModel: controller ? controller.pluginModel : null
    readonly property var summaryEntries: controller ? controller.settingsSummaryModel : null
    readonly property var environmentInfo: controller ? controller.environmentInfo : ({})
    readonly property var provider: UiDefaults.safeProvider(providerEntries.length > 0 ? providerEntries[0] : UiDefaults.provider())
    readonly property int activePluginCount: controller ? controller.activePluginCount : 0
    readonly property int summaryColumns: root.width > 1500 ? 3 : 1
    readonly property int pluginCount: (root.pluginModel && root.pluginModel.count !== undefined) ? root.pluginModel.count : 0
    readonly property string themeMode: controller ? controller.themeMode : "light"
    readonly property var sectionMap: ({
        "appearance": appearanceSection,
        "provider": providerSection,
        "plugins": pluginSection,
        "workspace": workspaceSection,
        "export": exportSection,
        "advanced": advancedSection
    })

    Component.onCompleted: appearanceSection.expanded = true

    function expand(categoryId, targetSection) {
        currentCategory = categoryId
        if (targetSection)
            targetSection.expanded = true
        Qt.callLater(function() {
            if (!targetSection)
                return
            suppressSync = true
            var targetY = rightContent.y + targetSection.y
            contentFlick.contentY = Math.max(0, Math.min(targetY - 12, contentFlick.contentHeight - contentFlick.height))
            syncTimer.restart()
        })
    }

    function syncCurrentCategory() {
        if (suppressSync)
            return
        var pivot = contentFlick.contentY + 36
        var sections = [
            { id: "appearance", item: appearanceSection },
            { id: "provider", item: providerSection },
            { id: "plugins", item: pluginSection },
            { id: "workspace", item: workspaceSection },
            { id: "export", item: exportSection },
            { id: "advanced", item: advancedSection }
        ]
        var nextCategory = currentCategory
        for (var i = 0; i < sections.length; ++i) {
            var candidate = sections[i]
            if (pivot >= candidate.item.y - 8)
                nextCategory = candidate.id
        }
        currentCategory = nextCategory
    }

    Timer {
        id: syncTimer
        interval: 180
        repeat: false
        onTriggered: root.suppressSync = false
    }

    RowLayout {
        anchors.fill: parent
        spacing: 18

        Rectangle {
            Layout.preferredWidth: 220
            Layout.maximumWidth: 220
            Layout.fillHeight: true
            radius: 6
            color: root.theme.panelRaised
            border.color: root.theme.border
            border.width: 1

            Column {
                id: navColumn
                anchors.fill: parent
                anchors.margins: 14
                spacing: 10

                Text {
                    text: "设置分类"
                    color: root.theme.text
                    font.pixelSize: 15
                    font.weight: Font.DemiBold
                }

                InteractiveChip { theme: root.theme; width: parent.width; text: "外观"; checked: root.currentCategory === "appearance"; onClicked: root.expand("appearance", appearanceSection) }
                InteractiveChip { theme: root.theme; width: parent.width; text: "模型接口"; checked: root.currentCategory === "provider"; onClicked: root.expand("provider", providerSection) }
                InteractiveChip { theme: root.theme; width: parent.width; text: "插件"; checked: root.currentCategory === "plugins"; onClicked: root.expand("plugins", pluginSection) }
                InteractiveChip { theme: root.theme; width: parent.width; text: "工作区 / 数据目录"; checked: root.currentCategory === "workspace"; onClicked: root.expand("workspace", workspaceSection) }
                InteractiveChip { theme: root.theme; width: parent.width; text: "导出 / 编译"; checked: root.currentCategory === "export"; onClicked: root.expand("export", exportSection) }
                InteractiveChip { theme: root.theme; width: parent.width; text: "高级 / 调试"; checked: root.currentCategory === "advanced"; onClicked: root.expand("advanced", advancedSection) }

                Item { height: 1; width: 1 }
            }
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.fillHeight: true
            radius: 6
            color: "transparent"

            Flickable {
                id: contentFlick
                anchors.fill: parent
                contentWidth: width
                contentHeight: rightContent.implicitHeight
                clip: true
                boundsBehavior: Flickable.StopAtBounds
                onContentYChanged: root.syncCurrentCategory()

                ScrollBar.vertical: AutoHideScrollBar { theme: root.theme }
                ScrollBar.horizontal: AutoHideScrollBar { theme: root.theme }

                Column {
                    id: rightContent
                    width: contentFlick.width
                    spacing: 18

                    Rectangle {
                        width: parent.width
                        radius: 6
                        color: root.theme.panelRaised
                        border.color: root.theme.border
                        border.width: 1
                        implicitHeight: summaryColumn.implicitHeight + 30

                        Column {
                            id: summaryColumn
                            anchors.fill: parent
                            anchors.margins: 15
                            spacing: 12

                            Text {
                                text: "设置总览"
                                color: root.theme.text
                                font.pixelSize: 16
                                font.weight: Font.DemiBold
                            }

                            GridView {
                                id: summaryGrid
                                width: parent.width
                                height: contentHeight
                                implicitHeight: contentHeight
                                interactive: false
                                clip: true
                                cellWidth: root.summaryColumns > 1 ? (width - (root.summaryColumns - 1) * 12) / root.summaryColumns : width
                                cellHeight: 112
                                model: root.summaryEntries

                                delegate: Item {
                                    id: summaryDelegate
                                    required property string title
                                    required property string value
                                    required property string detail
                                    required property string state
                                    readonly property string entryTitle: title || ""
                                    readonly property string entryValue: value || ""
                                    readonly property string entryDetail: detail || ""
                                    readonly property string entryState: state || ""
                                    width: summaryGrid.cellWidth
                                    height: summaryGrid.cellHeight

                                    MetricTile {
                                        anchors.fill: parent
                                        theme: root.theme
                                        label: summaryDelegate.entryTitle
                                        value: summaryDelegate.entryValue
                                        detail: summaryDelegate.entryDetail
                                        tone: summaryDelegate.entryState === "light" || summaryDelegate.entryState === "dark" ? "accent" : "neutral"
                                    }
                                }
                            }
                        }
                    }

                    Column {
                        width: parent.width
                        spacing: 14

                        InteractiveExpander {
                            id: appearanceSection
                            objectName: "appearanceSection"
                            width: parent.width
                            theme: root.theme
                            title: "外观"
                            subtitle: "主题与界面样式。"
                            onToggled: if (expanded) root.currentCategory = "appearance"

                            Row {
                                spacing: 8
                                InfoPill { text: root.themeMode === "light" ? "浅色模式" : "夜间模式"; fillColor: root.theme.accentSurface; borderColor: root.theme.accentOutline; textColor: root.theme.anchor }
                                InfoPill { text: root.activePluginCount + " 个插件已启用"; fillColor: root.theme.panelInset; borderColor: root.theme.border; textColor: root.theme.textMuted }
                            }

                            Text {
                                width: parent.width
                                text: "保持深蓝层级与矩形风格。"
                                color: root.theme.textSoft
                                wrapMode: Text.Wrap
                            }

                            InteractiveButton {
                                theme: root.theme
                                text: root.themeMode === "light" ? "切换到夜间模式" : "切换到浅色模式"
                                onClicked: if (root.controller) root.controller.toggleTheme()
                            }
                        }

                        InteractiveExpander {
                            id: providerSection
                            objectName: "providerSection"
                            width: parent.width
                            theme: root.theme
                            title: "模型接口"
                            subtitle: "接口与模型。"
                            onToggled: if (expanded) root.currentCategory = "provider"

                            GridLayout {
                                width: parent.width
                                columns: root.width > 1540 ? 2 : 1
                                columnSpacing: 12
                                rowSpacing: 12

                                InteractiveTextField { id: baseUrlField; theme: root.theme; width: parent.width; placeholderText: "Base URL"; text: root.provider.base_url || "" }
                                InteractiveTextField { id: apiKeyField; theme: root.theme; width: parent.width; placeholderText: "API Key"; echoMode: TextInput.Password; text: root.provider.api_key || "" }
                                InteractiveTextField { id: modelField; theme: root.theme; width: parent.width; placeholderText: "默认模型"; text: root.provider.default_model || "" }
                                InteractiveTextField { id: analysisModelField; theme: root.theme; width: parent.width; placeholderText: "分析模型"; text: root.provider.analysis_model || "" }
                            }

                            Row {
                                spacing: 10
                                InteractiveButton { theme: root.theme; text: "保存配置"; tone: "accent"; onClicked: if (root.controller) root.controller.savePrimaryProvider(baseUrlField.text, apiKeyField.text, modelField.text, analysisModelField.text, true) }
                                InteractiveButton { theme: root.theme; text: "连通性测试"; onClicked: if (root.controller) root.controller.testPrimaryProvider() }
                            }
                        }

                        InteractiveExpander {
                            id: pluginSection
                            objectName: "pluginSection"
                            width: parent.width
                            theme: root.theme
                            title: "插件"
                            subtitle: "查看与启停插件。"
                            onToggled: if (expanded) root.currentCategory = "plugins"

                            ListView {
                                width: parent.width
                                height: contentHeight
                                implicitHeight: contentHeight
                                interactive: false
                                clip: true
                                spacing: 10
                                reuseItems: true
                                model: root.pluginModel

                                delegate: Rectangle {
                                    readonly property bool hasIssue: !!load_error
                                    width: ListView.view.width
                                    radius: 6
                                    color: MotionCore.mixColor(root.theme.panelInset, root.theme.accentSurface, pluginInteraction.frameStrength * 0.16 + pluginInteraction.settleStrength * 0.10)
                                    border.color: hasIssue
                                                  ? MotionCore.mixColor(root.theme.border, root.theme.danger, 0.70)
                                                  : MotionCore.mixColor(root.theme.border, root.theme.accentOutline, pluginInteraction.frameStrength * 0.68 + pluginInteraction.settleStrength * 0.22)
                                    border.width: 1
                                    implicitHeight: pluginColumn.implicitHeight + 22

                                    Behavior on color {
                                        ColorAnimation { duration: MotionCore.duration("panel", root.theme) }
                                    }

                                    Behavior on border.color {
                                        ColorAnimation { duration: MotionCore.duration("panel", root.theme) }
                                    }

                                    InteractionState {
                                        id: pluginInteraction
                                        enabledInput: root.enabled
                                        visibleInput: root.visible
                                        hoveredInput: pluginHover.hovered
                                        pressedInput: false
                                        focusedInput: false
                                        busyInput: false
                                        selectedInput: !!plugin_enabled
                                    }

                                    SignalAccent {
                                        anchors.fill: parent
                                        active: pluginInteraction.settleStrength > 0.16
                                        hovered: pluginInteraction.hovered
                                        pressed: pluginInteraction.pressed
                                        accentColor: root.theme.anchor
                                        neutralColor: root.theme.accentSoft
                                        edge: hasIssue ? "left" : "frame"
                                        radius: 6
                                    }

                                    HoverHandler {
                                        id: pluginHover
                                        enabled: root.visible
                                    }

                                    Column {
                                        id: pluginColumn
                                        anchors.left: parent.left
                                        anchors.leftMargin: 12
                                        anchors.right: parent.right
                                        anchors.rightMargin: 12
                                        anchors.top: parent.top
                                        anchors.topMargin: 10
                                        spacing: 8

                                        RowLayout {
                                            width: parent.width
                                            spacing: 10

                                            ColumnLayout {
                                                Layout.fillWidth: true
                                                spacing: 4

                                                Text {
                                                    Layout.fillWidth: true
                                                    text: (name || "") + "  " + (version || "")
                                                    color: MotionCore.mixColor(root.theme.text, root.theme.anchor, pluginInteraction.textStrength * 0.28 + pluginInteraction.settleStrength * 0.20)
                                                    font.weight: Font.DemiBold
                                                    elide: Text.ElideRight

                                                    Behavior on color {
                                                        ColorAnimation { duration: MotionCore.duration("fast", root.theme) }
                                                    }
                                                }

                                                Text {
                                                    Layout.fillWidth: true
                                                    text: description || ""
                                                    color: MotionCore.mixColor(root.theme.textSoft, root.theme.textMuted, pluginInteraction.textStrength * 0.44)
                                                    wrapMode: Text.Wrap
                                                    maximumLineCount: 2
                                                    elide: Text.ElideRight

                                                    Behavior on color {
                                                        ColorAnimation { duration: MotionCore.duration("fast", root.theme) }
                                                    }
                                                }
                                            }

                                            InteractiveButton {
                                                theme: root.theme
                                                text: plugin_enabled ? "停用" : "启用"
                                                selected: !!plugin_enabled
                                                onClicked: if (root.controller) root.controller.setPluginEnabled(plugin_id, !plugin_enabled)
                                            }
                                        }

                                        Row {
                                            spacing: 8
                                            InfoPill { text: builtin ? "内置" : "外部"; fillColor: root.theme.panelRaised; borderColor: root.theme.border; textColor: root.theme.textMuted }
                                            InfoPill { text: state_label || ""; fillColor: plugin_enabled ? root.theme.accentSurface : root.theme.panelRaised; borderColor: plugin_enabled ? root.theme.accentOutline : root.theme.border; textColor: plugin_enabled ? root.theme.anchor : root.theme.textMuted }
                                        }

                                        Text {
                                            text: (author || "") + "  ·  " + (capabilities || "")
                                            color: MotionCore.mixColor(root.theme.textMuted, root.theme.textSoft, pluginInteraction.textStrength * 0.34)
                                            width: parent.width
                                            elide: Text.ElideRight
                                        }

                                        Text {
                                            visible: hasIssue
                                            text: load_error || ""
                                            color: root.theme.danger
                                            width: parent.width
                                            wrapMode: Text.Wrap
                                        }
                                    }
                                }
                            }

                            Text {
                                visible: root.pluginCount === 0
                                width: parent.width
                                text: "当前没有可展示的插件条目。"
                                color: root.theme.textSoft
                                wrapMode: Text.Wrap
                            }
                        }

                        InteractiveExpander {
                            id: workspaceSection
                            objectName: "workspaceSection"
                            width: parent.width
                            theme: root.theme
                            title: "工作区 / 数据目录"
                            subtitle: "工作区与目录。"
                            onToggled: if (expanded) root.currentCategory = "workspace"

                            Text { width: parent.width; text: "工作区文件：" + (root.environmentInfo.workspaceFile || ""); color: root.theme.text; wrapMode: Text.Wrap }
                            Text { width: parent.width; text: "草稿目录：" + (root.environmentInfo.draftsDir || ""); color: root.theme.textMuted; wrapMode: Text.Wrap }
                            Text { width: parent.width; text: "下载目录：" + (root.environmentInfo.downloadsDir || ""); color: root.theme.textMuted; wrapMode: Text.Wrap }
                            Text { width: parent.width; text: "LaTeX 目录：" + (root.environmentInfo.latexDir || ""); color: root.theme.textMuted; wrapMode: Text.Wrap }
                            Text { width: parent.width; text: "插件目录：" + (root.environmentInfo.pluginsDir || ""); color: root.theme.textMuted; wrapMode: Text.Wrap }
                        }

                        InteractiveExpander {
                            id: exportSection
                            objectName: "exportSection"
                            width: parent.width
                            theme: root.theme
                            title: "导出 / 编译"
                            subtitle: "模板、编译与导出。"
                            onToggled: if (expanded) root.currentCategory = "export"

                            Row {
                                spacing: 8
                                InfoPill { text: (root.environmentInfo.templateCount || 0) + " 个模板"; fillColor: root.theme.panelInset; borderColor: root.theme.border; textColor: root.theme.textMuted }
                                InfoPill { text: root.environmentInfo.xelatexAvailable ? "XeLaTeX 可用" : "XeLaTeX 未就绪"; fillColor: root.environmentInfo.xelatexAvailable ? root.theme.accentSurface : root.theme.note; borderColor: root.environmentInfo.xelatexAvailable ? root.theme.accentOutline : root.theme.border; textColor: root.environmentInfo.xelatexAvailable ? root.theme.anchor : root.theme.warning }
                            }

                            Text {
                                width: parent.width
                                text: "这里只显示当前状态。"
                                color: root.theme.textSoft
                                wrapMode: Text.Wrap
                            }
                        }

                        InteractiveExpander {
                            id: advancedSection
                            objectName: "advancedSection"
                            width: parent.width
                            theme: root.theme
                            title: "高级 / 调试"
                            subtitle: "底层状态与调试信息。"
                            onToggled: if (expanded) root.currentCategory = "advanced"

                            Row {
                                spacing: 8
                                InfoPill { text: root.environmentInfo.nativeAvailable ? "Native Bridge 已接入" : "Native Bridge 未接入"; fillColor: root.environmentInfo.nativeAvailable ? root.theme.accentSurface : root.theme.panelInset; borderColor: root.environmentInfo.nativeAvailable ? root.theme.accentOutline : root.theme.border; textColor: root.environmentInfo.nativeAvailable ? root.theme.anchor : root.theme.textMuted }
                            }

                            Text {
                                width: parent.width
                                text: "查看桥接与环境状态。"
                                color: root.theme.textSoft
                                wrapMode: Text.Wrap
                            }
                        }
                    }
                }
            }
        }
    }
}
