/* Copyright (C) 2023 Interactive Brokers LLC. All rights reserved. This code is subject to the terms
 * and conditions of the IB API Non-Commercial License or the IB API Commercial License, as applicable. */

package com.ib.api.dde.old.utils;

import com.ib.client.OrderType;
import com.ib.client.Types.SecType;

/** Class contains some utility methods */
public class OldUtils {

    public static boolean hasLmtPrice(OrderType orderType) {
        return orderType == OrderType.LMT || orderType == OrderType.STP_LMT || orderType == OrderType.REL || 
                orderType == OrderType.LIT || orderType == OrderType.LOC || orderType == OrderType.PEG_MKT || 
                orderType == OrderType.TRAIL_LIMIT || orderType == OrderType.PEG_MID || 
                orderType == OrderType.PEG_MID || orderType == OrderType.PASSV_REL || orderType == OrderType.PEG_PRIM_VOL;
    }

    public static boolean hasAuxPrice(OrderType orderType) {
        return orderType == OrderType.STP || orderType == OrderType.STP_LMT || orderType == OrderType.REL || 
                orderType == OrderType.LIT || orderType == OrderType.MIT || orderType == OrderType.PEG_MKT || 
                orderType == OrderType.TRAIL || orderType == OrderType.TRAIL_LIMIT ||  
                orderType == OrderType.PEG_MID || orderType == OrderType.PASSV_REL ||
                orderType == OrderType.PEG_PRIM_VOL;
    }
    
    public static boolean isExpDeriv(SecType secType) {
        return secType == SecType.OPT || secType == SecType.FUT || secType == SecType.FOP || secType == SecType.IOPT || secType == SecType.WAR;
    }

    public static boolean isOpt(SecType secType) {
        return secType == SecType.OPT || secType == SecType.FOP || secType == SecType.IOPT || secType == SecType.WAR;
    }
}
