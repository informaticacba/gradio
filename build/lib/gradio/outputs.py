"""
This module defines various classes that can serve as the `output` to an interface. Each class must inherit from
`OutputComponent`, and each class must define a path to its template. All of the subclasses of `OutputComponent` are
automatically added to a registry, which allows them to be easily referenced in other parts of the code.
"""

from gradio.component import Component
import numpy as np
import json
from gradio import processing_utils
import datetime
import operator
from numbers import Number
import warnings
import tempfile
import scipy

class OutputComponent(Component):
    """
    Output Component. All output components subclass this.
    """
    pass

class Textbox(OutputComponent):
    '''
    Component creates a textbox to render output text or number.
    Output type: Union[str, float, int]
    '''

    def __init__(self, type="str", label=None):
        '''
        Parameters:
        type (str): Type of value to be passed to component. "str" expects a string, "number" expects a float value.
        label (str): component name in interface.
        '''
        self.type = type
        super().__init__(label)

    def get_template_context(self):
        return {
            **super().get_template_context()
        }

    @classmethod
    def get_shortcut_implementations(cls):
        return {
            "text": {"type": "str"},
            "textbox": {"type": "str"},
            "number": {"type": "number"},
        }

    def postprocess(self, y):
        if self.type == "str":
            return y
        elif self.type == "number":
            return str(y)
        else:
            raise ValueError("Unknown type: " + self.type + ". Please choose from: 'str', 'number'")


class Label(OutputComponent):
    '''
    Component outputs a classification label, along with confidence scores of top categories if provided. Confidence scores are represented as a dictionary mapping labels to scores between 0 and 1.
    Output type: Union[Dict[str, float], str, int, float]
    '''

    LABEL_KEY = "label"
    CONFIDENCE_KEY = "confidence"
    CONFIDENCES_KEY = "confidences"

    def __init__(self, num_top_classes=None, label=None):
        '''
        Parameters:
        num_top_classes (int): number of most confident classes to show.
        label (str): component name in interface.
        '''
        self.num_top_classes = num_top_classes
        super().__init__(label)

    def postprocess(self, y):
        if isinstance(y, str) or isinstance(y, Number):
            return {"label": str(y)}
        elif isinstance(y, dict):
            sorted_pred = sorted(
                y.items(),
                key=operator.itemgetter(1),
                reverse=True
            )
            if self.num_top_classes is not None:
                sorted_pred = sorted_pred[:self.num_top_classes]
            return {
                self.LABEL_KEY: sorted_pred[0][0],
                self.CONFIDENCES_KEY: [
                    {
                        self.LABEL_KEY: pred[0],
                        self.CONFIDENCE_KEY: pred[1]
                    } for pred in sorted_pred
                ]
            }
        elif isinstance(y, int) or isinstance(y, float):
            return {self.LABEL_KEY: str(y)}
        else:
            raise ValueError("The `Label` output interface expects one of: a string label, or an int label, a "
                             "float label, or a dictionary whose keys are labels and values are confidences.")

    @classmethod
    def get_shortcut_implementations(cls):
        return {
            "label": {},
        }

    def rebuild(self, dir, data):
        """
        Default rebuild method for label
        """
        return json.loads(data)

class Image(OutputComponent):
    '''
    Component displays an output image. 
    Output type: Union[numpy.array, PIL.Image, str, matplotlib.pyplot]
    '''

    def __init__(self, type="numpy", plot=False, label=None):
        '''
        Parameters:
        type (str): Type of value to be passed to component. "numpy" expects a numpy array with shape (width, height, 3), "pil" expects a PIL image object, "file" expects a file path to the saved image, "plot" expects a matplotlib.pyplot object.
        plot (bool): DEPRECATED. Whether to expect a plot to be returned by the function.
        label (str): component name in interface.
        '''
        if plot:
            warnings.warn("The 'plot' parameter has been deprecated. Set parameter 'type' to 'plot' instead.", DeprecationWarning)
            self.type = "plot"
        else:
            self.type = type
        super().__init__(label)

    @classmethod
    def get_shortcut_implementations(cls):
        return {
            "image": {},
            "plot": {"type": "plot"},
            "pil": {"type": "pil"}
        }

    def postprocess(self, y):
        if self.type in ["numpy", "pil"]:
            if self.type == "pil":
                y = np.array(y)
            return processing_utils.encode_array_to_base64(y)
        elif self.type == "file":
            return processing_utils.encode_file_to_base64(y)
        elif self.type == "plot":
            return processing_utils.encode_plot_to_base64(y)
        else:
            raise ValueError("Unknown type: " + self.type + ". Please choose from: 'numpy', 'pil', 'file', 'plot'.")

    def rebuild(self, dir, data):
        """
        Default rebuild method to decode a base64 image
        """
        im = processing_utils.decode_base64_to_image(data)
        timestamp = datetime.datetime.now()
        filename = 'output_{}.png'.format(timestamp.
                                          strftime("%Y-%m-%d-%H-%M-%S"))
        im.save('{}/{}'.format(dir, filename), 'PNG')
        return filename

class KeyValues(OutputComponent):
    '''
    Component displays a table representing values for multiple fields. 
    Output type: Union[Dict, List[Tuple[str, Union[str, int, float]]]]
    '''

    def __init__(self, label=None):
        '''
        Parameters:
        label (str): component name in interface.
        '''
        super().__init__(label)

    def postprocess(self, y):
        if isinstance(y, dict):
            return list(y.items())
        elif isinstance(y, list):
            return y
        else:
            raise ValueError("The `KeyValues` output interface expects an output that is a dictionary whose keys are "
                             "labels and values are corresponding values.")

    @classmethod
    def get_shortcut_implementations(cls):
        return {
            "key_values": {},
        }


class HighlightedText(OutputComponent):
    '''
    Component creates text that contains spans that are highlighted by category or numerical value.
    Output is represent as a list of Tuple pairs, where the first element represents the span of text represented by the tuple, and the second element represents the category or value of the text.
    Output type: List[Tuple[str, Union[float, str]]]
    '''

    def __init__(self, color_map=None, label=None):
        '''
        Parameters:
        color_map (Dict[str, str]): Map between category and respective colors
        label (str): component name in interface.
        '''
        self.color_map = color_map
        super().__init__(label)

    def get_template_context(self):
        return {
            "color_map": self.color_map,
            **super().get_template_context()
        }

    @classmethod
    def get_shortcut_implementations(cls):
        return {
            "highlight": {},
        }

    def postprocess(self, y):
        return y


class Audio(OutputComponent):
    '''
    Creates an audio player that plays the output audio.
    Output type: Union[Tuple[int, numpy.array], str]
    '''

    def __init__(self, type="numpy", label=None):
        '''
        Parameters:
        type (str): Type of value to be passed to component. "numpy" returns a 2-set tuple with an integer sample_rate and the data numpy.array of shape (samples, 2), "file" returns a temporary file path to the saved wav audio file.
        label (str): component name in interface.
        '''
        self.type = type
        super().__init__(label)

    def get_template_context(self):
        return {
            **super().get_template_context()
        }

    @classmethod
    def get_shortcut_implementations(cls):
        return {
            "audio": {},
        }

    def postprocess(self, y):
        if self.type in ["numpy", "file"]:
            if self.type == "numpy":
                file = tempfile.NamedTemporaryFile()
                scipy.io.wavfile.write(file, y[0], y[1])                
                y = file.name
            return processing_utils.encode_file_to_base64(y, type="audio", ext="wav")
        else:
            raise ValueError("Unknown type: " + self.type + ". Please choose from: 'numpy', 'file'.")


class JSON(OutputComponent):
    '''
    Used for JSON output. Expects a JSON string or a Python object that is JSON serializable. 
    Output type: Union[str, Any]
    '''

    def __init__(self, label=None):
        '''
        Parameters:
        label (str): component name in interface.
        '''
        super().__init__(label)

    def postprocess(self, y):
        if isinstance(y, str):
            return json.dumps(y)
        else:
            return y


    @classmethod
    def get_shortcut_implementations(cls):
        return {
            "json": {},
        }


class HTML(OutputComponent):
    '''
    Used for HTML output. Expects an HTML valid string. 
    Output type: str
    '''

    def __init__(self, label=None):
        '''
        Parameters:
        label (str): component name in interface.
        '''
        super().__init__(label)


    @classmethod
    def get_shortcut_implementations(cls):
        return {
            "html": {},
        }


class File(OutputComponent):
    '''
    Used for file output. Expects a string path to a file if `return_path` is True.     
    Output type: Union[bytes, str]
    '''

    def __init__(self, type="file", label=None):
        '''
        Parameters:
        type (str): Type of value to be passed to component. "file" expects a  file path, "str" exxpects a string to be returned as a file, "binary" expects an bytes object to be returned as a file.  
        label (str): component name in interface.
        '''
        super().__init__(label)


    @classmethod
    def get_shortcut_implementations(cls):
        return {
            "file": {},
        }


class Dataframe(OutputComponent):
    """
    Component displays 2D output through a spreadsheet interface.
    Output type: Union[pandas.DataFrame, numpy.array, List[Union[str, float]], List[List[Union[str, float]]]]
    """

    def __init__(self, headers=None, type="pandas", label=None):
        '''
        Parameters:
        headers (List[str]): Header names to dataframe.
        type (str): Type of value to be passed to component. "pandas" for pandas dataframe, "numpy" for numpy array, or "array" for Python array.
        label (str): component name in interface.
        '''
        self.type = type
        self.headers = headers
        super().__init__(label)


    def get_template_context(self):
        return {
            "headers": self.headers,
            **super().get_template_context()
        }

    @classmethod
    def get_shortcut_implementations(cls):
        return {
            "dataframe": {"type": "pandas"},
            "numpy": {"type": "numpy"},
            "matrix": {"type": "array"},
            "list": {"type": "array"},
        }

    def postprocess(self, y):
        if self.type == "pandas":
            return {"headers": list(y.columns), "data": y.values.tolist()}
        elif self.type in ("numpy", "array"):
            if self.type == "numpy":
                y = y.tolist()
            if len(y) == 0 or not isinstance(y[0], list):
                y = [y]
            return {"data": y} 
        else:
            raise ValueError("Unknown type: " + self.type + ". Please choose from: 'pandas', 'numpy', 'array'.")
