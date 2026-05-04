def pytest_itemcollected(item):
    """
    Pytest Hook: Overrides the default test execution terminal output.
    
    Instead of printing the standard file path and function name (e.g., test_app.py::test_login), 
    this hook intercepts the test collection phase and replaces the internal identifier 
    with the test function's human-readable docstring.
    """
    
    # Verify the test function has an associated docstring before attempting an override.
    # The item.obj represents the actual Python test function/method object.
    if item.obj.__doc__:
        
        # Strip leading/trailing whitespace to ensure clean, aligned console formatting.
        doc = item.obj.__doc__.strip()
        
        # Determine if the test is dynamically generated via @pytest.mark.parametrize.
        # Parameterized tests have a 'callspec' attribute containing their specific inputs.
        if hasattr(item, 'callspec'):
            
            # Append the specific parameterization ID (the specific scenario/edge case) 
            # to the base docstring so individual test variations remain distinguishable in the terminal.
            item._nodeid = f"{doc} [{item.callspec.id}]"
        else:
            # For standard, non-parameterized tests, simply replace the system node ID 
            # with the human-readable docstring.
            item._nodeid = doc