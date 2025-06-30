#!/usr/bin/env python3
"""
Test the simplified inventory positioning logic
"""

class MockInventory:
    def __init__(self, width=6, height=8):
        self.width = width
        self.height = height
        self.children = []
    
    def find_free_spot(self):
        """Find the first available spot in the inventory grid using a simple counter approach."""
        # Count how many items we currently have
        current_item_count = len(self.children)
        
        # Convert count to grid position (row-major order)
        if current_item_count >= self.width * self.height:
            return None  # Inventory full
        
        # Calculate grid position based on item count
        # Row-major order: items fill left to right, then top to bottom
        x = current_item_count % self.width
        y = current_item_count // self.width
        
        return x, y

def test_simple_positioning():
    print("Testing simplified inventory positioning logic...")
    
    inventory = MockInventory()
    
    # Test the first 12 positions
    for i in range(12):
        spot = inventory.find_free_spot()
        print(f"Item {i}: spot {spot}")
        # Simulate adding the item
        inventory.children.append(f"Item{i}")
    
    print("\nExpected pattern:")
    print("(0,0), (1,0), (2,0), (3,0), (4,0), (5,0),")
    print("(0,1), (1,1), (2,1), (3,1), (4,1), (5,1)")

if __name__ == "__main__":
    test_simple_positioning()