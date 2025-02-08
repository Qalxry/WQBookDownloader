import os
import json
import atexit
from typing import Literal, Optional, Any, MutableMapping


class JsonProxy(MutableMapping):
    """
    A proxy class that interfaces with a JSON file and allows attribute-based
    read and write access. It supports optional autosave functionality and can
    operate in different modes to handle reading, writing, or both.
    Attributes:
        _JsonProxy__json_file (str): The path to the JSON file to be managed.
        _JsonProxy__mode (Literal["r", "w", "rw"]): The mode in which the file is accessed.
        _JsonProxy__save_after_change_count (Optional[int]): Number of changes after which
            the data is persisted automatically. If None, data is saved on every change.
        _JsonProxy__change_count (int): Internal counter tracking the number of modifications
            since the last save.
    """

    def __init__(
        self,
        json_file: str,
        mode: Literal["r", "w", "rw"] = "r",
        save_after_change_count: Optional[int] = None,
    ):
        """
        Initialize the JsonProxy instance, load data from the specified JSON file,
        and register a save operation to occur automatically when the program
        exits.

        Args:
            json_file (str): Path to the JSON file.

            mode (Literal["r", "w", "rw"]): Access mode for the JSON file:
                - "r" for read-only,
                - "w" for write-only,
                - "rw" for read/write.

            save_after_change_count (Optional[int]): Number of attribute changes after which
                data is saved automatically. If None, data is saved every time an attribute
                is changed.
        """
        self._JsonProxy__json_file = json_file
        self._JsonProxy__mode = mode
        self._JsonProxy__save_after_change_count = save_after_change_count
        self._JsonProxy__change_count = 0
        self.load()
        atexit.register(self.save)  # 在程序退出时保存数据

    def load(self):
        """
        Load data from the JSON file into the current instance's attributes.
        If the file is not found or is invalid JSON, behavior depends on the mode:
        - If mode is "w", create an empty file if it doesn't exist.
        - If mode is "r" and the file doesn't exist or is corrupt, raise FileNotFoundError.
        """

        if self._JsonProxy__mode == "w":
            if not os.path.exists(self._JsonProxy__json_file):
                os.makedirs(os.path.dirname(self._JsonProxy__json_file) or "./", exist_ok=True)
                with open(self._JsonProxy__json_file, "w") as f:
                    json.dump({}, f)
        else:
            try:
                with open(self._JsonProxy__json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for key, value in data.items():
                        setattr(self, key, value)
            except (FileNotFoundError, json.JSONDecodeError):
                if self._JsonProxy__mode == "r":
                    raise FileNotFoundError(f"File not found: {self._JsonProxy__json_file}")

    def save(self):
        """
        Save the current instance's non-private attributes to the JSON file,
        respecting the mode setting. If the mode is "r", this method does nothing.
        """
        if self._JsonProxy__mode == "r":
            return
        data = {key: value for key, value in self.__dict__.items() if not key.startswith("_JsonProxy_")}
        os.makedirs(os.path.dirname(self._JsonProxy__json_file) or "./", exist_ok=True)
        with open(self._JsonProxy__json_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def __setattr__(self, name: str, value: Any):
        """
        Override default behavior to automatically trigger a save operation
        (or increment a change counter) whenever a non-private attribute changes.
        """
        super().__setattr__(name, value)
        if name.startswith("_JsonProxy_") or "_JsonProxy__save_after_change_count" not in self.__dict__:
            return
        if self._JsonProxy__save_after_change_count is None:
            self.save()
        elif self._JsonProxy__change_count >= self._JsonProxy__save_after_change_count:
            self.save()
            self._JsonProxy__change_count = 0
        else:
            self._JsonProxy__change_count += 1

    def __delattr__(self, name: str):
        """
        Override default behavior to automatically trigger a save operation
        (or increment a change counter) whenever a non-private attribute is deleted.
        """
        super().__delattr__(name)
        if name.startswith("_JsonProxy_") or "_JsonProxy__save_after_change_count" not in self.__dict__:
            return
        if self._JsonProxy__save_after_change_count is None:
            self.save()
        elif self._JsonProxy__change_count >= self._JsonProxy__save_after_change_count:
            self.save()
            self._JsonProxy__change_count = 0
        else:
            self._JsonProxy__change_count += 1
    
    def __getitem__(self, key: str):
        """
        Return the value of the specified attribute.
        """
        return getattr(self, key)
    
    def __setitem__(self, key: str, value: Any):
        """
        Set the value of the specified attribute.
        """
        setattr(self, key, value)
        
    def __delitem__(self, key: str):
        """
        Delete the specified attribute.
        """
        delattr(self, key)
        
    def __contains__(self, key: str):
        """
        Check if the specified attribute exists.
        """
        return key in self.__dict__
    
    def keys(self):
        """
        Return a list of non-private attribute names.
        """
        return [key for key in self.__dict__ if not key.startswith("_JsonProxy_")]
    
    def values(self):
        """
        Return a list of non-private attribute values.
        """
        return [value for key, value in self.__dict__.items() if not key.startswith("_JsonProxy_")]
    
    def items(self):
        """
        Return a list of non-private attribute name-value pairs.
        """
        return [(key, value) for key, value in self.__dict__.items() if not key.startswith("_JsonProxy_")]
    
    def clear(self):
        """
        Clear all non-private attributes.
        """
        for key in self.keys():
            delattr(self, key)
            
    def get(self, key: str, default: Any = None):
        """
        Return the value of the specified attribute, or a default value if the attribute does not exist.
        """
        return getattr(self, key, default)
    
    def pop(self, key: str, default: Any = None):
        """
        Remove the specified attribute and return its value, or a default value if the attribute does not exist.
        """
        value = self.get(key, default)
        delattr(self, key)
        return value
    
    def update(self, *args, **kwargs):
        """
        Update the attributes of the instance with the specified key-value pairs.
        """
        for key, value in dict(*args, **kwargs).items():
            setattr(self, key, value)
            
    def setdefault(self, key: str, default: Any = None):
        """
        Return the value of the specified attribute, or set it to the default value if the attribute does not exist.
        """
        if key not in self:
            setattr(self, key, default)
        return getattr(self, key)
    
    def copy(self):
        """
        Return a shallow copy of the instance.
        """
        return {key: value for key, value in self.items()}
    
    def popitem(self):
        """
        Remove and return an arbitrary attribute name-value pair.
        """
        key = next(iter(self.keys()))
        value = self.pop(key)
        return key, value
    
    def __repr__(self):
        """
        Return a string representation of the instance.
        """
        return f"{self.__class__.__name__}({self.__dict__})"
    
    def __iter__(self):
        """
        Return an iterator over the non-private attributes of the instance.
        """
        return iter({key: value for key, value in self.__dict__.items() if not key.startswith("_JsonProxy_")})

    def __len__(self):
        """
        Return the number of non-private attributes of the instance.
        """
        return len([key for key in self.__dict__ if not key.startswith("_JsonProxy_")])

    def __enter__(self):
        """
        Enter the runtime context related to this object, returning self.
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Exit the runtime context and save data to the JSON file.
        """
        self.save()  # 退出上下文时保存数据

    def __str__(self):
        """
        Return a string representation of all non-private attributes of the instance.
        """
        return str({key: value for key, value in self.__dict__.items() if not key.startswith("_JsonProxy_")})
