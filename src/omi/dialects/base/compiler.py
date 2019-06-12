from omi import structure


class Compiler:
    def visit(self, obj, *args, **kwargs):
        if isinstance(obj, structure.Compilable):
            meth = getattr(self, "visit_{name}".format(name=obj.__compiler_name__))
            return meth(obj, *args, **kwargs)
        else:
            return obj

    def visit_context(self, context: structure.Context, *args, **kwargs):
        raise NotImplementedError

    def visit_contributor(self, contributor: structure.Contribution, *args, **kwargs):
        raise NotImplementedError

    def visit_language(self, language: structure.Language, *args, **kwargs):
        raise NotImplementedError

    def visit_spatial(self, spatial: structure.Spatial, *args, **kwargs):
        raise NotImplementedError

    def visit_temporal(self, temporal: structure.Temporal, *args, **kwargs):
        raise NotImplementedError

    def visit_timestamp_orientation(
        self, ts_orientation: structure.TimestampOrientation, *args, **kwargs
    ):
        raise NotImplementedError

    def visit_source(self, source: structure.Source, *args, **kwargs):
        raise NotImplementedError

    def visit_license(self, lic: structure.License, *args, **kwargs):
        raise NotImplementedError

    def visit_resource(self, resource: structure.Resource, *args, **kwargs):
        raise NotImplementedError

    def visit_schema(self, context: structure.Schema, *args, **kwargs):
        raise NotImplementedError

    def visit_dialect(self, context: structure.Dialect, *args, **kwargs):
        raise NotImplementedError

    def visit_field(self, field: structure.Field, *args, **kwargs):
        raise NotImplementedError

    def visit_foreign_key(self, foreign_key: structure.ForeignKey, *args, **kwargs):
        raise NotImplementedError

    def visit_reference(self, reference: structure.Reference, *args, **kwargs):
        raise NotImplementedError

    def visit_review(self, review: structure.Review, *args, **kwargs):
        raise NotImplementedError

    def visit_meta_comment(self, comment: structure.MetaComment, *args, **kwargs):
        raise NotImplementedError

    def visit_metadata(self, metadata: structure.OEPMetadata, *args, **kwargs):
        raise NotImplementedError
