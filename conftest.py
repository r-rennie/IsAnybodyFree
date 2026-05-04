def pytest_itemcollected(item):
    """Forces Pytest to use your custom docstrings in the terminal."""
    
    # Check if the test has a """triple quote""" docstring
    if item.obj.__doc__:
        # Clean up the text
        doc = item.obj.__doc__.strip()
        
        # Check if it's a parameterized test (like your Edge Cases)
        if hasattr(item, 'callspec'):
            # Combine the docstring with your custom 'ids' label
            item._nodeid = f"{doc} [{item.callspec.id}]"
        else:
            # For standard tests, just use the docstring
            item._nodeid = doc