from collections import defaultdict
import math


clengths_metric = (6, 7.5, 9, 10.5, 12)
"""Standard rebar commercial lengths in meters: 6, 7.5, 9, 10.5, 12"""

clengths_english = (20, 25, 30, 35, 40)
"""Standard rebar commercial lengths in feet: 20, 25, 30, 35, 40"""


estimate_result = defaultdict(int)
excess_inventory = defaultdict(int)
cut_record = []


def record_cut(length_produced:float, 
               qty_produced:int, 
               type_produced:str,
               wlength:float, 
               type_wlength:str, 
               get_log:bool=False
               ) -> list:
    
    """
    Helper function to save record of produced cut and excess.

    Args:
        length_produced (float): Length of produced cut of rebar.
        qty_produced (int): Quantity of produced cut of rebar.
        clength (float): Length used to produce **cut_length** (from commercial length or excess).
        type (str): Type of produced cut.
        get_log (bool): Default is **False**. Returns the updated log of cut if **True**.
    
    Returns:
        cut_record (list): A list of dict where each dict corresponds to a recorded cut.
        **get_log** must be **True** for the function to return this list.
    
    """

    record = {
        "produced_length": length_produced,
        "produced_qty": qty_produced,
        "produced_type": type_produced,
        "from_length": wlength,
        "from_length_type": type_wlength,
    }
    
    cut_record.append(record)

    return cut_record if get_log else None


def get_optimal_clength(cut_length:float, clengths:list=clengths_metric) -> float:
    """Returns optimal commercial length based on produced waste/residue of cut length."""

    residues = [(round(clength % cut_length, 3), clength) for clength in clengths]
    return min(residues)[1]


def estimate_clength(
        cut_length:float, 
        reqd_qty:int, 
        wclength:float, 
        ) -> int:
    
    """
    Returns the quantity of the chosen rebar commercial length 
    based on the required quantity of cut length.

    Args:
        cut_length (float): Length of rebar to produce.
        reqd_qty (int): Quantity of **cut_length** to produce.
        wclength (float): Length of rebar to use. Must be from commercial length.

    Returns:
        reqd_qty_wclength (int): Quantity of **wclength** needed.
    
    """

    yield_qty = int(wclength // cut_length)
    reqd_qty_wclength = math.ceil(reqd_qty / yield_qty)
    record_cut(cut_length, reqd_qty, "cut length", wclength, "new rebar")

    yield_waste = round(wclength - cut_length * yield_qty, 3)
    yield_waste_qty = reqd_qty // yield_qty

    if yield_waste > 0 and yield_waste_qty > 0:
        excess_inventory[yield_waste] += yield_waste_qty
        record_cut(yield_waste, yield_waste_qty, "excess", wclength, "new rebar")

    if (reqd_qty / yield_qty) < reqd_qty_wclength:
        total_length = wclength * reqd_qty_wclength
        total_reqd = cut_length * reqd_qty
        waste_from_cut = yield_waste * yield_waste_qty

        waste_leftover = round(total_length - total_reqd - waste_from_cut, 3)
        excess_inventory[waste_leftover] += 1
        record_cut(waste_leftover, 1, "excess", wclength, "new rebar")

    return reqd_qty_wclength


def use_excess_length(
        cut_length:float, 
        reqd_qty:int, 
        ) -> int:
    
    """
    Utilize available excess lengths to produce cut lengths.
    Returns the adjusted required quantity of cut length to produce.
    
    """

    if not excess_inventory or reqd_qty == 0:
        return reqd_qty

    wqty = reqd_qty
    sorted_winventory = sorted(excess_inventory.items(), reverse=True)

    for excess_length, available_excess in sorted_winventory:
        if excess_length < cut_length:
            continue

        qty_per_excess = int(excess_length // cut_length)
        total_available_qty = qty_per_excess * available_excess

        # Case when chosen excess length is enough or not sufficient to produce required quantity
        # Used all available stock of chosen excess length
        if wqty >= total_available_qty:
            record_cut(cut_length, total_available_qty, "cut length", excess_length, "excess rebar")
            excess_inventory.pop(excess_length, None)

            remain_excess = round(excess_length % cut_length, 3)
            if remain_excess > 0:
                excess_inventory[remain_excess] += available_excess
                record_cut(remain_excess, available_excess, "excess", excess_length, "excess rebar")

            wqty -= total_available_qty
            
        # Case when chosen excess length is more than sufficient to produce required quantity
        # Used portions of available stock of chosen excess length
        else:
            qty_used_full_excess = math.ceil(wqty / qty_per_excess)
            qty_leftover = wqty % qty_per_excess
            record_cut(cut_length, wqty, "cut length", excess_length, "excess rebar")

            excess_inventory[excess_length] -= qty_used_full_excess
            if excess_inventory[excess_length] <= 0:
                excess_inventory.pop(excess_length, None)

            # Remaining excess length from full cuts
            remain_excess = round(excess_length % cut_length, 3)
            if remain_excess > 0:
                excess_inventory[remain_excess] += qty_used_full_excess
                record_cut(remain_excess, qty_used_full_excess, "excess", excess_length, "excess rebar")

            # Remaining excess length from leftover
            if qty_leftover > 0:
                total_length_excess = excess_length * available_excess
                total_remain_excess = remain_excess * qty_used_full_excess
                total_length_reqd = cut_length * wqty
                
                leftover_excess = round(total_length_excess - total_remain_excess - total_length_reqd, 3)
                excess_inventory[leftover_excess] += 1
                record_cut(leftover_excess, 1, "excess", excess_length, "excess rebar")

            wqty = 0
            
    return wqty


def get_estimate(cut_schedule:list, wclengths:list) -> list:
    """Wrapper function for functions used to estimate rebars."""

    # Ensures program runs at clean state
    estimate_result.clear()
    excess_inventory.clear()
    cut_record.clear()

    # Sort cut schedule starting at largest cut length
    input_cut_lengths = sorted(cut_schedule, reverse=True)

    # Estimate required quantity for each cut length
    for cut_length, quantity in input_cut_lengths:
        
        # Use excess lengths from previous cut if applicable
        wqty = use_excess_length(cut_length=cut_length, reqd_qty=quantity)
        if wqty <= 0:
            break
        
        # Pick optimal rebar length then use it for estimate
        clength = get_optimal_clength(cut_length=cut_length, clengths=wclengths)
        qty_clength = estimate_clength(cut_length=cut_length, reqd_qty=wqty, wclength=clength)

        # Record result
        estimate_result[clength] += qty_clength

    return estimate_result, excess_inventory, cut_record