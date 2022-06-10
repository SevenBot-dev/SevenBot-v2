from discord import Embed
import yaml

from src.const.color import Color

from .. import lang


class LocaleEmbed(Embed):
    def __init__(self, data: lang.LocaleGroup, **formats):
        self.locale_data = data
        super().__init__()
        self.title = self.locale_data("title", **formats)
        self.description = self.locale_data("description", **formats)
        with open("src/embed.yml") as file:
            embed_data = yaml.safe_load(file)
        try:
            for part in self.locale_data.code.split("."):
                embed_data = embed_data[part]
        except KeyError:
            embed_data = {}
        color = embed_data.get("color")
        if color is None:
            pass
        elif isinstance(color, int):
            self.color = embed_data.get("color")
        elif color.startswith("#"):
            self.color = int(color[1:], 16)
        else:
            self.color = Color[color]._value_
        self.set_footer(
            text=self.locale_data("footer", None, **formats), icon_url=embed_data.get("footer_icon_url", None)
        )
        self.set_thumbnail(url=embed_data.get("thumbnail_url", None))
        if self.locale_data("author.name", embed_data.get("author_name", None)):
            self.set_author(
                name=self.locale_data("author.name", embed_data.get("author_name", None), **formats),
                url=self.locale_data("author.url", embed_data.get("author_url", None), **formats),
                icon_url=embed_data.get("author_icon_url", None),
            )
        self.set_image(url=embed_data.get("image_url", None))
        for field_name, field_data in self.locale_data("fields", {}).items():
            self.add_field(
                name=field_name.format(**formats),
                value=field_data.format(**formats),
            )
