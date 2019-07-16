Dialects
********

The OMI tool handles all metadata in an internal data structure that covers the
relevant information needed to describe data. Different metadata formats
(e.g. the OEP metadata format) can be **parsed** into this structure or
**compiled** from it.

Therefore, OMI uses the notion of **Parser** and **Compiler**.

.. automodule:: omi.structure
   :members:

.. autoclass:: omi.dialects.base.parser.Parser
   :members:

.. autoclass:: omi.dialects.base.compiler.Compiler
   :members:
