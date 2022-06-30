.. _dialect:

========
Dialects
========

This section discusses the concepts of :class:`~omi.dialects.base.dialect.Parser`, :class:`~omi.dialects.base.dialect.Compiler` and
:class:`~omi.dialects.base.dialect.Dialect`

The OMI tool handles all metadata in an internal data structure that covers the
relevant information needed to describe data. Different metadata formats
(e.g. the OEP metadata format) can be **parsed** into this structure or
**compiled** from it.

Therefore, OMI uses the notion of **Parser** and **Compiler**. A
:class:`~omi.dialects.base.dialect.Dialect` combines the functionalities of
:class:`~omi.dialects.base.dialect.Parser`,
:class:`~omi.dialects.base.dialect.Compiler` and adds some convenience methods
to it. Each dialect has an id that can be used to call it via the  :ref:`command line interface<cli>`

.. _available_dialects:

Available dialects are:
    - `oep-v1.3`
    - `oep-v1.4`
    - `oep-rdf-v1.4`
    - `oep-v1.5`

.. autoclass:: omi.dialects.base.dialect.Parser
   :members:

.. autoclass:: omi.dialects.base.dialect.Compiler
   :members:

.. autoclass:: omi.dialects.base.dialect.Dialect
   :members:


