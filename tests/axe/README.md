# Vendored axe-core

`axe.min.js` is axe-core **4.14.0** (MPL-2.0), taken unmodified from the
`axe-core` npm package and used only by `tests/test_accessibility.py`. It is a test
dependency: nothing from this directory is inlined into `index.html`.

Update it with:

```bash
npm pack axe-core@latest
tar -xzf axe-core-*.tgz
cp package/axe.min.js tests/axe/axe.min.js
cp package/LICENSE tests/axe/LICENSE
```

Keep the version in the first line of this file in step with `tests/test_accessibility.py`.

https://github.com/dequelabs/axe-core
