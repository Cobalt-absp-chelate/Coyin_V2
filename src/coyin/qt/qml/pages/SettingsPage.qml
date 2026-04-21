import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../components"
import "../support/UiDefaults.js" as UiDefaults

ScrollView {
    id: root
    property var controller: null
    property var theme: UiDefaults.safeTheme(UiDefaults.theme())
    property string currentCategory: "appearance"

    readonly property var providerEntries: controller ? controller.providerEntries : []
    readonly property var pluginEntries: controller ? controller.pluginEntries : []
    readonly property var summaryEntries: controller ? controller.settingsSummaryModel : null
    readonly property var environmentInfo: controller ? controller.environmentInfo : ({})
    readonly property var provider: UiDefaults.safeProvider(providerEntries.length > 0 ? providerEntries[0] : UiDefaults.provider())
    readonly property int activePluginCount: controller ? controller.activePluginCount : 0
    readonly property string themeMode: controller ? controller.themeMode : "light"

    function expand(categoryId, targetSection) {
        currentCategory = categoryId
        targetSection.expanded = true
    }

    contentWidth: availableWidth

    RowLayout {
        width: root.availableWidth
        spacing: 18

        Rectangle {
            Layout.preferredWidth: 220
            Layout.maximumWidth: 220
            Layout.alignment: Qt.AlignTop
            radius: 6
            color: root.theme.panelRaised
            border.color: root.theme.border
            border.width: 1
            implicitHeight: navColumn.implicitHeight + 28

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

                InteractiveChip { theme: root.theme; text: "外观"; checked: root.currentCategory === "appearance"; onClicked: root.expand("appearance", appearanceSection) }
                InteractiveChip { theme: root.theme; text: "模型接口"; checked: root.currentCategory === "provider"; onClicked: root.expand("provider", providerSection) }
                InteractiveChip { theme: root.theme; text: "插件"; checked: root.currentCategory === "plugins"; onClicked: root.expand("plugins", pluginSection) }
                InteractiveChip { theme: root.theme; text: "工作区 / 数据目录"; checked: root.currentCategory === "workspace"; onClicked: root.expand("workspace", workspaceSection) }
                InteractiveChip { theme: root.theme; text: "导出 / 编译"; checked: root.currentCategory === "export"; onClicked: root.expand("export", exportSection) }
                InteractiveChip { theme: root.theme; text: "高级 / 调试"; checked: root.currentCategory === "advanced"; onClicked: root.expand("advanced", advancedSection) }
            }
        }

        ColumnLayout {
            Layout.fillWidth: true
            Layout.alignment: Qt.AlignTop
            spacing: 18

            Rectangle {
                Layout.fillWidth: true
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

                    GridLayout {
                        width: parent.width
                        columns: root.availableWidth > 1280 ? 3 : 1
                        columnSpacing: 12
                        rowSpacing: 12

                        Repeater {
                            model: root.summaryEntries
                            delegate: MetricTile {
                                Layout.fillWidth: true
                                theme: root.theme
                                label: model.title
                                value: model.value
                                detail: model.detail
                                tone: model.state === "light" || model.state === "dark" ? "accent" : "neutral"
                            }
                        }
                    }
                }
            }

            Column {
                Layout.fillWidth: true
                spacing: 14

                InteractiveExpander {
                    id: appearanceSection
                    width: parent.width
                    theme: root.theme
                    title: "外观"
                    subtitle: "配色、主题和主界面节奏统一在一个入口里，默认保持收纳。"

                    Row {
                        spacing: 8
                        InfoPill { text: root.themeMode === "light" ? "浅色模式" : "夜间模式"; fillColor: root.theme.accentSurface; borderColor: root.theme.accentOutline; textColor: root.theme.anchor }
                        InfoPill { text: root.activePluginCount + " 个插件已启用"; fillColor: root.theme.panelInset; borderColor: root.theme.border; textColor: root.theme.textMuted }
                    }

                    Text {
                        width: parent.width
                        text: "当前界面继续保持深蓝层级、矩形和小圆角矩形，交互强调统一走同一套底层高亮描边。"
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
                    width: parent.width
                    theme: root.theme
                    title: "模型接口"
                    subtitle: "主接口和分析模型都收进同一段，避免设置页一打开就是长表单。"

                    GridLayout {
                        width: parent.width
                        columns: root.availableWidth > 1240 ? 2 : 1
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
                    width: parent.width
                    theme: root.theme
                    title: "插件"
                    subtitle: "插件状态默认收起，需要时再展开查看和启停。"

                    Repeater {
                        model: root.pluginEntries
                        delegate: Rectangle {
                            width: parent.width
                            radius: 6
                            color: root.theme.panelInset
                            border.color: root.theme.border
                            border.width: 1
                            implicitHeight: pluginColumn.implicitHeight + 22

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

                                        Text { text: name + "  " + version; color: root.theme.text; font.weight: Font.DemiBold; elide: Text.ElideRight }
                                        Text { text: description; color: root.theme.textSoft; width: parent.width; wrapMode: Text.Wrap; maximumLineCount: 2; elide: Text.ElideRight }
                                    }

                                    InteractiveButton {
                                        theme: root.theme
                                        text: plugin_enabled ? "停用" : "启用"
                                        selected: plugin_enabled
                                        onClicked: if (root.controller) root.controller.setPluginEnabled(plugin_id, !plugin_enabled)
                                    }
                                }

                                Row {
                                    spacing: 8
                                    InfoPill { text: builtin ? "内置" : "外部"; fillColor: root.theme.panelRaised; borderColor: root.theme.border; textColor: root.theme.textMuted }
                                    InfoPill { text: state_label; fillColor: plugin_enabled ? root.theme.accentSurface : root.theme.panelRaised; borderColor: plugin_enabled ? root.theme.accentOutline : root.theme.border; textColor: plugin_enabled ? root.theme.anchor : root.theme.textMuted }
                                }

                                Text { text: author + "  ·  " + capabilities; color: root.theme.textMuted; width: parent.width; elide: Text.ElideRight }
                                Text { visible: load_error !== ""; text: load_error; color: root.theme.danger; width: parent.width; wrapMode: Text.Wrap }
                            }
                        }
                    }

                    Text {
                        visible: root.pluginEntries.length === 0
                        width: parent.width
                        text: "当前没有可展示的插件条目。"
                        color: root.theme.textSoft
                        wrapMode: Text.Wrap
                    }
                }

                InteractiveExpander {
                    id: workspaceSection
                    width: parent.width
                    theme: root.theme
                    title: "工作区 / 数据目录"
                    subtitle: "把工作区路径和常用目录归在一类，避免被模型配置淹没。"

                    Text { width: parent.width; text: "工作区文件：" + (root.environmentInfo.workspaceFile || ""); color: root.theme.text; wrapMode: Text.Wrap }
                    Text { width: parent.width; text: "草稿目录：" + (root.environmentInfo.draftsDir || ""); color: root.theme.textMuted; wrapMode: Text.Wrap }
                    Text { width: parent.width; text: "下载目录：" + (root.environmentInfo.downloadsDir || ""); color: root.theme.textMuted; wrapMode: Text.Wrap }
                    Text { width: parent.width; text: "LaTeX 目录：" + (root.environmentInfo.latexDir || ""); color: root.theme.textMuted; wrapMode: Text.Wrap }
                    Text { width: parent.width; text: "插件目录：" + (root.environmentInfo.pluginsDir || ""); color: root.theme.textMuted; wrapMode: Text.Wrap }
                }

                InteractiveExpander {
                    id: exportSection
                    width: parent.width
                    theme: root.theme
                    title: "导出 / 编译"
                    subtitle: "把模板数量、LaTeX 编译器状态和导出准备情况单独收纳。"

                    Row {
                        spacing: 8
                        InfoPill { text: (root.environmentInfo.templateCount || 0) + " 个模板"; fillColor: root.theme.panelInset; borderColor: root.theme.border; textColor: root.theme.textMuted }
                        InfoPill { text: root.environmentInfo.xelatexAvailable ? "XeLaTeX 可用" : "XeLaTeX 未就绪"; fillColor: root.environmentInfo.xelatexAvailable ? root.theme.accentSurface : root.theme.note; borderColor: root.environmentInfo.xelatexAvailable ? root.theme.accentOutline : root.theme.border; textColor: root.environmentInfo.xelatexAvailable ? root.theme.anchor : root.theme.warning }
                    }

                    Text {
                        width: parent.width
                        text: "导出链路仍然保留在写作窗口和 LaTeX 工作区里，这里只提供汇总状态，不把整页变成开发者面板。"
                        color: root.theme.textSoft
                        wrapMode: Text.Wrap
                    }
                }

                InteractiveExpander {
                    id: advancedSection
                    width: parent.width
                    theme: root.theme
                    title: "高级 / 调试"
                    subtitle: "保留必要的运行态观测，但默认不打扰日常使用。"

                    Row {
                        spacing: 8
                        InfoPill { text: root.environmentInfo.nativeAvailable ? "Native Bridge 已接入" : "Native Bridge 未接入"; fillColor: root.environmentInfo.nativeAvailable ? root.theme.accentSurface : root.theme.panelInset; borderColor: root.environmentInfo.nativeAvailable ? root.theme.accentOutline : root.theme.border; textColor: root.environmentInfo.nativeAvailable ? root.theme.anchor : root.theme.textMuted }
                    }

                    Text {
                        width: parent.width
                        text: "当前高级区主要用于确认底层桥接、模板和编译环境，不再把所有调试文本直接堆满设置首页。"
                        color: root.theme.textSoft
                        wrapMode: Text.Wrap
                    }
                }
            }
        }
    }
}
