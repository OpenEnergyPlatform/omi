import datetime

from metadata_tool.dialects.oep.parser import JSONParser_1_3
from metadata_tool.dialects.oep.compiler import JSONCompiler
from metadata_tool import structure


def metadata_conversion(old_sql, new_sql, user, user_email):
    """ Conversion of an existing metadata file to a newer version by using the above functions.

    Parameters
    ----------

    old_sql: str
        The path to the file containing the old sql file.
    new_sql: str
        The filename of the new sql file.
    user: str
        The name of the user for the 'contributors' section
    user_email: str
        The email address of the user.

    Returns
    -------
    """

    parser = JSONParser_1_3()
    metadata = parser.parse_from_file(old_sql)

    metadata.contributors.append(
        structure.Contributor(
            title=user,
            email=user_email,
            date=datetime.now,
            obj=None,
            comment="Update metadata to v1.3 using metadata conversion tool",
        )
    )

    compiler = JSONCompiler()
    with open(new_sql) as out_file:
        out_file.write(compiler.visit(metadata))
