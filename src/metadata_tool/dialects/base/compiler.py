from metadata_tool import structure


class Compiler:

    def visit(self, obj):
        if isinstance(obj, structure.Compilable):
            meth = getattr(self,
                           "visit_{name}".format(name=obj.__compiler_name__))
            return meth(obj)
        else:
            return obj

    def visit_context(self, context: structure.Context):
        raise NotImplementedError

    def visit_contributor(self, contributor: structure.Contributor):
        raise NotImplementedError

    def visit_language(self, language: structure.Language):
        raise NotImplementedError

    def visit_spatial(self, spatial: structure.Spatial):
        raise NotImplementedError

    def visit_temporal(self, temporal: structure.Temporal):
        raise NotImplementedError

    def visit_source(self, source: structure.Source):
        raise NotImplementedError

    def visit_license(self, lic: structure.License):
        raise NotImplementedError

    def visit_resource(self, resource: structure.Resource):
        raise NotImplementedError

    def visit_schema(self, context: structure.Schema):
        raise NotImplementedError

    def visit_field(self, field: structure.Field):
        raise NotImplementedError

    def visit_foreign_key(self, foreign_key: structure.ForeignKey):
        raise NotImplementedError

    def visit_reference(self, reference: structure.Reference):
        raise NotImplementedError

    def visit_review(self, review: structure.Review):
        raise NotImplementedError

    def visit_meta_comment(self, comment: structure.MetaComment):
        raise NotImplementedError

    def visit_meta_meta_data(self, metadata: structure.MetaMetaData):
        raise NotImplementedError

    def visit_metadata(self, metadata: structure.OEPMetadata):
        raise NotImplementedError
