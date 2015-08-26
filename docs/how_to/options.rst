#######
Options
#######

Main usage is described in :doc:`how_to/usage`.

``follow_placeholders`` - The 'follow_placeholders' class property is
introduced and is, by default, True. If set to False in the implmementing class
allows the class to implement reversion, but without considering the placeholder
field(s) it contains.

To apply aldryn-reversion to a class but ignore the contents of its
placeholderfield(s), register it like so: ::

    @reversion.register(
        adapter_cls=ContentEnabledVersionAdapter,
        follow_placeholders=False,
        revision_manager=reversion.default_revision_manager,
    )
    class MyModel(models.Model):
        # Changes to plugins inside this placeholder fields are not revisioned
        # but theif we change the placeholder object this field points to, that
        # change will be picked up by reversion.
        placeholder = PlaceholderField()

instead of using the shortcut decorator ``@version-controlled-content``.