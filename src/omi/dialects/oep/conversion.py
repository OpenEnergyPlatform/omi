import datetime

from omi import structure
from omi.dialects.oep.compiler import JSONCompiler
from omi.dialects.oep.parser import JSONParser_1_3


def metadata_conversion(old_sql, new_sql, user, user_email):
    """ Conversion of an existing metadata file to a newer version

    Parameters
    ----------

    old_sql: str
        The path to the file containing the old sql file.
    new_sql: str
        The filename of the new sql file.
    user: str
        The name of the user for the 'contributions' section
    user_email: str
        The email address of the user.

    Returns
    -------
    """

    parser = JSONParser_1_3()
    metadata = parser.parse_from_file(old_sql)

    metadata.contributors.append(
        structure.Contribution(
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
