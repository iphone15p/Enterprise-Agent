def fib(n):
    """
    Compute the nth Fibonacci number (0-indexed).
    
    Args:
        n (int): A non-negative integer.
        
    Returns:
        int: The nth Fibonacci number (F₀=0, F₁=1, F₂=1, F₃=2, ...).
        
    Raises:
        ValueError: If n is negative.
    """
    if not isinstance(n, int) or n < 0:
        raise ValueError("n must be a non-negative integer")
    
    if n == 0:
        return 0
    elif n == 1:
        return 1
    
    # Iterative computation with O(1) space
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b