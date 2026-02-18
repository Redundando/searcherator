---
Package: logorator
Version: 1.0.7
Source: https://pypi.org/project/logorator/
Fetched: 2026-02-18 18:13:53
---

# Logorator

A decorator-based logging library for Python with support for both synchronous and asynchronous functions.

## Features

- Simple decorator-based logging for function calls
- Full support for both synchronous and asynchronous functions
- Function execution time measurement
- ANSI color-coded output for better readability
- Optional file output for logs
- Configurable output formats
- Custom note insertion during execution

## Installation

```bash
pip install logorator
```

## Basic Usage

### Synchronous Functions

```python
from logorator import Logger

@Logger()
def add(a, b):
    return a + b

result = add(3, 5)

# Output:
# Running add 
#   3
#   5
# Finished add Time elapsed: 0.10 ms
```

### Asynchronous Functions

```python
from logorator import Logger
import asyncio

@Logger()
async def fetch_data(url):
    # Simulating network request
    await asyncio.sleep(1)
    return f"Data from {url}"

async def main():
    result = await fetch_data("https://example.com")

asyncio.run(main())

# Output:
# Running async fetch_data 
#   https://example.com
# Finished async fetch_data (https://example.com) Time elapsed: 1,000.23 ms
```

## API Reference

### `Logger` Class

#### Constructor

```python
Logger(silent=None, mode="normal", override_function_name=None)
```

- **silent** (bool, optional): If True, suppresses logging output. Defaults to None, which uses the global `Logger.SILENT` value.
- **mode** (str, optional): Determines the logging format. Options are 'normal' (default) or 'short' (tab-separated).
- **override_function_name** (str, optional): If provided, uses this name in logs instead of the actual function name.

#### Class Methods

##### `set_silent(silent=True)`

Sets the global silent mode for all Logger instances.

- **silent** (bool): If True, suppresses all logging output globally. Defaults to True.

##### `set_output(filename=None)`

Sets the global output file for all Logger instances.

- **filename** (str | None): The path to the file where logs should be written. If None, logs are written to the console.

##### `note(note="", mode="normal")`

Logs a custom note.

- **note** (str): The custom message to log. Defaults to an empty string.
- **mode** (str): The logging mode ('normal' or 'short'). Defaults to 'normal'.

##### `log(message="", end="")`

Static method to write a log message.

- **message** (str): The message to log.
- **end** (str): The string appended after the message (default is empty string).

#### Instance Methods

##### `eol()`

Returns the end-of-line character(s) based on the current mode.

- Returns: `\t` for "short" mode, `\n` for "normal" mode.

##### `__call__(func)`

Makes Logger instances callable as decorators. Automatically detects if the function is asynchronous and wraps it accordingly.

- **func** (callable): The function to decorate.

### Visual Differentiation

Logorator visually differentiates between synchronous and asynchronous functions:

- Asynchronous functions are prefixed with `async` in purple color
- Asynchronous functions display their first argument in the completion log

## Advanced Usage

### Custom Notes

Insert custom notes in your code:

```python
from logorator import Logger

@Logger()
def process_data(data):
    # Processing...
    Logger.note("Data validation complete")
    # More processing...
    return result
```

### File Output

Direct logs to a file instead of the console:

```python
from logorator import Logger

# Set up file logging
Logger.set_output("logs/application.log")

@Logger()
def main():
    # Application logic
    pass

main()
```

### Short Mode

Use short mode for more compact output with tab-separated entries:

```python
from logorator import Logger

@Logger(mode="short")
def calculate(a, b):
    return a + b

result = calculate(5, 3)
```

### Toggle Logging

Enable or disable logging globally:

```python
from logorator import Logger
import os

# Disable in production
if os.environ.get("ENVIRONMENT") == "production":
    Logger.set_silent(True)
```

### Custom Function Name

Display a custom name in logs:

```python
@Logger(override_function_name="DatabaseConnect")
async def connect_to_db(url, username, password):
    # Connection logic
    pass
```

## Combining with Other Decorators

When using with other decorators, typically place Logger as the outermost (top) decorator:

```python
@Logger()
@cache
def expensive_calculation(x):
    # Calculation logic
    pass
```
