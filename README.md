daylight-saving-time
====================

Development
-----------

### Cheat sheet

#### Module not found

```
$ pytest
...
E   ModuleNotFoundError: No module named 'dst_notifier'
```

```
$ vim pyproject.toml
```

```toml
[tool.pytest.ini_options]
pythonpath = ["."]
```

Or:

```
touch tests/__init__.py
```

### TODO

- Add typing
- ~~Add directories:~~
    ~~+ etc/~~
    ~~+ var/~~
