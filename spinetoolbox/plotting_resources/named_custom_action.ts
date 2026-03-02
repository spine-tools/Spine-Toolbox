import {CustomAction, CustomActionView} from "models/tools/actions/custom_action"
import type * as p from "core/properties"
import {Menu, MenuItem} from "models/ui/menus"

export class NamedCustomActionView extends CustomActionView {
  declare model: NamedCustomAction
}

export namespace NamedCustomAction {
  export type Attrs = p.AttrsOf<Props>
  export type Props = CustomAction.Props & {
    tool_label: p.Property<string>
  }
}

export interface NamedCustomAction extends NamedCustomAction.Attrs {}

export class NamedCustomAction extends CustomAction {
  declare properties: NamedCustomAction.Props
  declare __view_type__: NamedCustomActionView

  constructor(attrs?: Partial<NamedCustomAction.Attrs>) {
    super(attrs)
  }

  static {
    this.prototype.default_view = NamedCustomActionView

    this.define<NamedCustomAction.Props>(({Str}) => ({
      tool_label: [Str, "Custom Action"],
    }))
  }

  // Override menu_item() to use tool_label instead of tool_name
  // This is what creates the context menu entry
  override menu_item(): MenuItem {
    const item = new MenuItem({
      icon: this.computed_icon,
      label: this.tool_label,  // Use custom label here instead of tool_name
      tooltip: this.tooltip != this.tool_label ? this.tooltip : undefined,
      checked: () => this.active,
      disabled: () => this.disabled,
      action: () => this.do.emit(undefined),
    })

    const submenu = this.menu
    if (submenu != null) {
      item.menu = new Menu({items: submenu})
    }
    return item
  }
}
