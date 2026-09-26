import torch

def generate_test_suites(num_samples=100):
    # Deterministic generation for reproducibility
    torch.manual_seed(42)
    
    # 1. Normal Test Set: Random noise inputs pretending to be normalized CIFAR-10 images
    normal_inputs = torch.randn(num_samples, 3, 32, 32)
    
    # 2. Trigger Test Set: Same as normal but with a synthetic patch in the top-left corner
    trigger_inputs = normal_inputs.clone()
    # Apply a 6x6 red patch trigger
    trigger_inputs[:, 0, 0:6, 0:6] = 2.5 # High red channel
    trigger_inputs[:, 1, 0:6, 0:6] = -2.5 # Low green
    trigger_inputs[:, 2, 0:6, 0:6] = -2.5 # Low blue
    
    return normal_inputs, trigger_inputs
