# lxsocdoc: Document your LiteX SoC Automatically

`lxsocdoc` lets you take a synthesized LiteX SoC and generate full
register-level documentation.  Additionally, it will generate `.svd` files,
suitable for use with various header generation programs.

## Usage

To use `lxsocdoc`, import the module and call `lxsocdoc.generate_docs(soc, path)`.
You can also generate an SVD file.  For example:

```python
import lxsocdoc

...
    soc = BaseSoC(platform)
    builder = Builder(soc)
    vns = builder.build()
    soc.do_exit(vns)
    lxsocdoc.generate_docs(soc, "build/documentation/")
    lxsocdoc.generate_svd(soc, "build/software")
```

After you build your design, you will have a Sphinx documentation source available
in the above directory.  To build this into a target document, use `sphinx-build`.

For example:

`sphinx-build -M html build/documentation/ build/documentation/_build`

## Required Software

You must have `sphinx` and `sphinx.wavedrom` installed in order to build
the documentation.  These can be installed with pip:

```
$ pip install sphinxcontrib-wavedrom sphinx
```
