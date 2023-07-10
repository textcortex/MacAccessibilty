# Mac Accessbility API Handler
This project is designed to enable communication between the Mac Accessibility API and other software applications. This communication is facilitated by the use of APIs, allowing for the exchange of data between applications and the Mac Accessibility API. This exchange of data will enable users to access the full range of accessibility features available on Mac systems, such as voice recognition, text-to-speech, and the ability to interact with applications using only keyboard or mouse commands. By providing greater access to accessibility features, this project will help Mac users to better utilize their systems and make computing more accessible to all.

# Usage
## Installation

Putting the software to use requires set-up beforehand; namely, installation.

```
python setup.py bdist_wheel
cd dist
pip install *.whl
```

## Example

```py
from textCortex.mac_accessible import MacAccessbility

def call_back(notification,data):
    print(notification)
    print(data)


macAccessbility=MacAccessbility(call_back)
macAccessbility.start()

```