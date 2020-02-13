# lxsocdoc: Document your LiteX SoC Automatically

`lxsocdoc` lets you take a synthesized LiteX SoC and generate full
register-level documentation.  Additionally, it will generate `.svd` files,
suitable for use with various header generation programs.

**This project has been merged into litex**

This project is no longer separately maintained.  To continue using lxsocdoc with upstream litex, replace `import lxsocdoc` with `import litex.soc.doc as lxsocdoc`:

```python
# import lxsocdoc
import litex.soc.doc as lxsocdoc
```

This repository is no longer compatible with newer releases of litex.  However, the upstream version is fully compatible with this API.
