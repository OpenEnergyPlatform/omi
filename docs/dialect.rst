========
Dialects
========


This section discusses the concepts of :class:`~omi.dialects.base.dialect.Parser`, :class:`~omi.dialects.base.dialect.Compiler` and
:class:`~omi.dialects.base.dialect.Dialect`

The OMI tool handles all metadata in an internal data structure that covers the
relevant information needed to describe data. Different metadata formats
(e.g. the OEP metadata format) can be **parsed** into this structure or
**compiled** from it.

Therefore, OMI uses the notion of **Parser** and **Compiler**.



.. autoclass:: omi.dialects.base.dialect.Parser
   :members:

.. autoclass:: omi.dialects.base.dialect.Compiler
   :members:

.. autoclass:: omi.dialects.base.dialect.Dialect
   :members:


