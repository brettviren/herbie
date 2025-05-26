import sys
import asyncio
#from herbie.amenu import BAIL, Item, Menu, task as spawn_menu
import rofi_menu

class MyItem(rofi_menu.Item):
    async def on_select(self, meta):
        sys.stderr.write(f'{meta}\n')
        return rofi_menu.Operation(rofi_menu.OP_OUTPUT, (
            "💢 simple\n"
            "💥 multi-\n"
            "💫 <b>line</b>\n"
            "💣 <i>text</i>\n"
        ))

menu = rofi_menu.Menu(prompt="Prompt", items=[MyItem()])
rofi_menu.run(menu)
