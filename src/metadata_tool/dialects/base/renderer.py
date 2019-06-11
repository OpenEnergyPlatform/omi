class Renderer:
    def render(self, inp, *args, **kwargs) -> str:
        """
        Transforms the given structure string into a string

        Parameters
        ----------
        inp
            The structure to render

        Returns
        -------
        str
            A string representation of `inp`
        """
        raise NotImplementedError

    @staticmethod
    def __unpack_file(*args, **kwargs):
        """

        Parameters
        ----------

        Returns
        -------

        """
        with open(*args, **kwargs) as inp:
            return inp.read()

    def render_to_file(self, inp, file_path, *args, **kwargs):
        with open(file_path, "w") as outfile:
            outfile.write(self.render(inp, *args, **kwargs))
