// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design implementation internals
// See Vhbm_controller_tb_simple.h for the primary calling header

#include "Vhbm_controller_tb_simple__pch.h"
#include "Vhbm_controller_tb_simple__Syms.h"
#include "Vhbm_controller_tb_simple___024root.h"

#ifdef VL_DEBUG
VL_ATTR_COLD void Vhbm_controller_tb_simple___024root___dump_triggers__stl(Vhbm_controller_tb_simple___024root* vlSelf);
#endif  // VL_DEBUG

VL_ATTR_COLD void Vhbm_controller_tb_simple___024root___eval_triggers__stl(Vhbm_controller_tb_simple___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vhbm_controller_tb_simple___024root___eval_triggers__stl\n"); );
    Vhbm_controller_tb_simple__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    vlSelfRef.__VstlTriggered.setBit(0U, (IData)(vlSelfRef.__VstlFirstIteration));
    vlSelfRef.__VstlTriggered.setBit(1U, ((IData)(vlSelfRef.hbm_controller_tb_simple__DOT__clk) 
                                          != (IData)(vlSelfRef.__Vtrigprevexpr___TOP__hbm_controller_tb_simple__DOT__clk__0)));
    vlSelfRef.__Vtrigprevexpr___TOP__hbm_controller_tb_simple__DOT__clk__0 
        = vlSelfRef.hbm_controller_tb_simple__DOT__clk;
    if (VL_UNLIKELY(((1U & (~ (IData)(vlSelfRef.__VstlDidInit)))))) {
        vlSelfRef.__VstlDidInit = 1U;
        vlSelfRef.__VstlTriggered.setBit(1U, 1U);
    }
#ifdef VL_DEBUG
    if (VL_UNLIKELY(vlSymsp->_vm_contextp__->debug())) {
        Vhbm_controller_tb_simple___024root___dump_triggers__stl(vlSelf);
    }
#endif
}
