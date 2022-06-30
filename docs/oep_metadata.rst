======================
Translations in Python
======================

.. testsetup:: *

    from omi.dialects.oep.dialect import OEP_V_1_3_Dialect, OEP_V_1_4_Dialect, OEP_V_1_5_Dialect

In order to perform the translation from one dialect to another, you need to
parse your input using the respective input dialect. As a minimal example, let's
say you have a metadata string in the outdated version 1.3 and aim to update it
to the more modern version 1.4.

Step 1: Parse it
****************

Your first step is to parse the given string using :class:`omi.dialects.oep.dialect.OEP_V_1_3_Dialect`.
For starters, we use the most basic metadata string: The empty dictionary

.. doctest::

    >>> inp = '{}'
    >>> dialect1_3 = OEP_V_1_3_Dialect()
    >>> parsed = dialect1_3.parse(inp)
    >>> parsed
    OEPMetadata(name=None,title=None,identifier=None,description=None,languages=None,keywords=None,publication_date=None,context=None,spatial=None,temporal=None,sources=None,license=None,contributions=None,resources=None,review=None,comment=None)

The input has been parsed into the internal structure i.e. an :class:`OEPMetadata`-object.

Step 2: Change it
*****************

If needed you can feel free to manipulate this string according to your use case.
Don't forget to document your changes under contributions (ToDo) ;)

In this example, we will add an identifier, as is required by OEP-Metadata v1.4

.. doctest::

    >>> parsed.identifier = "unique_id"
    >>> parsed
    OEPMetadata(name=None,title=None,identifier=unique_id,description=None,languages=None,keywords=None,publication_date=None,context=None,spatial=None,temporal=None,sources=None,license=None,contributions=None,resources=None,review=None,comment=None)

Step 3: Compile it
******************

Now that we have an :class:`OEPMetadata`-object we are happy with, we want to translate it to the
new metadata format by using the respective dialect

.. doctest::

    >>> dialect1_4 = OEP_V_1_4_Dialect()
    >>> dialect1_4.compile(parsed)
    {'id': 'unique_id', 'metaMetadata': {'metadataVersion': 'OEP-1.4.0', 'metadataLicense': {'name': 'CC0-1.0', 'title': 'Creative Commons Zero v1.0 Universal', 'path': 'https://creativecommons.org/publicdomain/zero/1.0/'}}}
