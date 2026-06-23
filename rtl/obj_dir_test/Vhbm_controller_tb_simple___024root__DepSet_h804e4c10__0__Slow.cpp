// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design implementation internals
// See Vhbm_controller_tb_simple.h for the primary calling header

#include "Vhbm_controller_tb_simple__pch.h"
#include "Vhbm_controller_tb_simple___024root.h"

VL_ATTR_COLD void Vhbm_controller_tb_simple___024root___eval_static__TOP(Vhbm_controller_tb_simple___024root* vlSelf);

VL_ATTR_COLD void Vhbm_controller_tb_simple___024root___eval_static(Vhbm_controller_tb_simple___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vhbm_controller_tb_simple___024root___eval_static\n"); );
    Vhbm_controller_tb_simple__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    Vhbm_controller_tb_simple___024root___eval_static__TOP(vlSelf);
    vlSelfRef.__Vtrigprevexpr___TOP__clk__0 = vlSelfRef.clk;
    vlSelfRef.__Vtrigprevexpr___TOP__hbm_controller_tb_simple__DOT__rst_n__0 = 0U;
}

VL_ATTR_COLD void Vhbm_controller_tb_simple___024root___eval_static__TOP(Vhbm_controller_tb_simple___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vhbm_controller_tb_simple___024root___eval_static__TOP\n"); );
    Vhbm_controller_tb_simple__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    vlSelfRef.hbm_controller_tb_simple__DOT__rst_n = 0U;
    vlSelfRef.hbm_controller_tb_simple__DOT__tb_req_valid = 0U;
    vlSelfRef.hbm_controller_tb_simple__DOT__tb_req_id = 0U;
    vlSelfRef.hbm_controller_tb_simple__DOT__tb_req_addr = 0ULL;
    vlSelfRef.hbm_controller_tb_simple__DOT__tb_req_rd_wr_n = 1U;
    vlSelfRef.hbm_controller_tb_simple__DOT__cycle = 0U;
    vlSelfRef.hbm_controller_tb_simple__DOT__resp_count = 0U;
}

VL_ATTR_COLD void Vhbm_controller_tb_simple___024root___eval_initial(Vhbm_controller_tb_simple___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vhbm_controller_tb_simple___024root___eval_initial\n"); );
    Vhbm_controller_tb_simple__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
}

VL_ATTR_COLD void Vhbm_controller_tb_simple___024root___eval_final(Vhbm_controller_tb_simple___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vhbm_controller_tb_simple___024root___eval_final\n"); );
    Vhbm_controller_tb_simple__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
}

#ifdef VL_DEBUG
VL_ATTR_COLD void Vhbm_controller_tb_simple___024root___dump_triggers__stl(Vhbm_controller_tb_simple___024root* vlSelf);
#endif  // VL_DEBUG
VL_ATTR_COLD bool Vhbm_controller_tb_simple___024root___eval_phase__stl(Vhbm_controller_tb_simple___024root* vlSelf);

VL_ATTR_COLD void Vhbm_controller_tb_simple___024root___eval_settle(Vhbm_controller_tb_simple___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vhbm_controller_tb_simple___024root___eval_settle\n"); );
    Vhbm_controller_tb_simple__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Init
    IData/*31:0*/ __VstlIterCount;
    CData/*0:0*/ __VstlContinue;
    // Body
    __VstlIterCount = 0U;
    vlSelfRef.__VstlFirstIteration = 1U;
    __VstlContinue = 1U;
    while (__VstlContinue) {
        if (VL_UNLIKELY(((0x64U < __VstlIterCount)))) {
#ifdef VL_DEBUG
            Vhbm_controller_tb_simple___024root___dump_triggers__stl(vlSelf);
#endif
            VL_FATAL_MT("/home/ic/JXTF/HBM/rtl/hbm_controller_tb_simple.sv", 9, "", "Settle region did not converge.");
        }
        __VstlIterCount = ((IData)(1U) + __VstlIterCount);
        __VstlContinue = 0U;
        if (Vhbm_controller_tb_simple___024root___eval_phase__stl(vlSelf)) {
            __VstlContinue = 1U;
        }
        vlSelfRef.__VstlFirstIteration = 0U;
    }
}

#ifdef VL_DEBUG
VL_ATTR_COLD void Vhbm_controller_tb_simple___024root___dump_triggers__stl(Vhbm_controller_tb_simple___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vhbm_controller_tb_simple___024root___dump_triggers__stl\n"); );
    Vhbm_controller_tb_simple__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    if ((1U & (~ vlSelfRef.__VstlTriggered.any()))) {
        VL_DBG_MSGF("         No triggers active\n");
    }
    if ((1ULL & vlSelfRef.__VstlTriggered.word(0U))) {
        VL_DBG_MSGF("         'stl' region trigger index 0 is active: Internal 'stl' trigger - first iteration\n");
    }
}
#endif  // VL_DEBUG

VL_ATTR_COLD void Vhbm_controller_tb_simple___024root___stl_sequent__TOP__0(Vhbm_controller_tb_simple___024root* vlSelf);

VL_ATTR_COLD void Vhbm_controller_tb_simple___024root___eval_stl(Vhbm_controller_tb_simple___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vhbm_controller_tb_simple___024root___eval_stl\n"); );
    Vhbm_controller_tb_simple__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    if ((1ULL & vlSelfRef.__VstlTriggered.word(0U))) {
        Vhbm_controller_tb_simple___024root___stl_sequent__TOP__0(vlSelf);
    }
}

extern const VlUnpacked<CData/*3:0*/, 256> Vhbm_controller_tb_simple__ConstPool__TABLE_hea14f260_0;

VL_ATTR_COLD void Vhbm_controller_tb_simple___024root___stl_sequent__TOP__0(Vhbm_controller_tb_simple___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vhbm_controller_tb_simple___024root___stl_sequent__TOP__0\n"); );
    Vhbm_controller_tb_simple__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Init
    CData/*2:0*/ hbm_controller_tb_simple__DOT__dut__DOT__best_priority;
    hbm_controller_tb_simple__DOT__dut__DOT__best_priority = 0;
    CData/*7:0*/ hbm_controller_tb_simple__DOT__dut__DOT__best_age;
    hbm_controller_tb_simple__DOT__dut__DOT__best_age = 0;
    CData/*0:0*/ hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit;
    hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit = 0;
    CData/*7:0*/ __Vtableidx1;
    __Vtableidx1 = 0;
    // Body
    vlSelfRef.hbm_controller_tb_simple__DOT__tb_req_ready 
        = (0x20U > (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue_count));
    vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue_empty 
        = (0U == (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue_count));
    vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0U;
    hbm_controller_tb_simple__DOT__dut__DOT__best_priority = 0U;
    hbm_controller_tb_simple__DOT__dut__DOT__best_age = 0U;
    vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit = 0U;
    vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__grant_valid = 0U;
    hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit = 0U;
    if (((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[4U] 
          >> 4U) & (0U == (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__state)))) {
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
            = (0xfffffffffULL & (((QData)((IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[3U])) 
                                  << 0x20U) | (QData)((IData)(
                                                              vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[2U]))));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch 
            = (0x1fU & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                                >> 0x1eU)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bg 
            = (7U & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                             >> 0x1aU)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_pch 
            = (1U & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                             >> 0x17U)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bank 
            = (0xfU & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                               >> 0x16U)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_row 
            = (0xffffU & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                                  >> 6U)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__Vfuncout 
            = (((((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__row_open 
                   >> ([&]() {
                                    vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__ch 
                                        = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                    vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__Vfuncout 
                                        = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__ch;
                                }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__Vfuncout))) 
                  & ((IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_pch) 
                     == (1U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_pch_reg 
                               >> ([&]() {
                                            vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__ch 
                                                = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                            vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__Vfuncout 
                                                = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__ch;
                                        }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__Vfuncout)))))) 
                 & ((IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bg) 
                    == ((0x5fU >= (0x7fU & ((IData)(3U) 
                                            * VL_EXTEND_II(32,5, 
                                                           ([&]() {
                                                    vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__ch 
                                                        = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                                    vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__Vfuncout 
                                                        = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__ch;
                                                }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__Vfuncout))))))
                         ? (7U & VL_SEL_IWII(96, vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_bg_reg, 
                                             (0x7fU 
                                              & ((IData)(3U) 
                                                 * 
                                                 VL_EXTEND_II(32,5, 
                                                              ([&]() {
                                                        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__ch 
                                                            = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                                        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__Vfuncout 
                                                            = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__ch;
                                                    }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__Vfuncout))))), 3U))
                         : 0U))) & ((IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bank) 
                                    == (0xfU & VL_SEL_IWII(128, vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_bank_reg, 
                                                           (0x7fU 
                                                            & VL_SHIFTL_III(7,32,32, 
                                                                            VL_EXTEND_II(32,5, 
                                                                                ([&]() {
                                                vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__ch 
                                                    = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                                vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__Vfuncout 
                                                    = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__ch;
                                            }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__Vfuncout))), 2U)), 4U)))) 
               & ((IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_row) 
                  == (0xffffU & VL_SEL_IWII(512, vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_row_reg, 
                                            (0x1ffU 
                                             & VL_SHIFTL_III(9,32,32, 
                                                             VL_EXTEND_II(32,5, 
                                                                          ([&]() {
                                            vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__ch 
                                                = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                            vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__Vfuncout 
                                                = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__ch;
                                        }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__Vfuncout))), 4U)), 0x10U))));
        hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit 
            = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__Vfuncout;
        if (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__grant_valid) {
            if (((IData)(hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit) 
                 & (~ (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit)))) {
                vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0U;
                hbm_controller_tb_simple__DOT__dut__DOT__best_priority 
                    = (7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[1U] 
                             >> 0xcU));
                hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                    = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0U] 
                                >> 4U));
                vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit 
                    = hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit;
            } else if (((IData)(hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit) 
                        & (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit))) {
                if (((7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[1U] 
                            >> 0xcU)) > (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_priority))) {
                    vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0U;
                    hbm_controller_tb_simple__DOT__dut__DOT__best_priority 
                        = (7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[1U] 
                                 >> 0xcU));
                    hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                        = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0U] 
                                    >> 4U));
                } else if (((7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[1U] 
                                   >> 0xcU)) == (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_priority))) {
                    if (((0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0U] 
                                   >> 4U)) < (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_age))) {
                        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0U;
                        hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                            = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0U] 
                                        >> 4U));
                    }
                }
            } else if ((1U & ((~ (IData)(hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit)) 
                              & (~ (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit))))) {
                if (((7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[1U] 
                            >> 0xcU)) > (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_priority))) {
                    vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0U;
                    hbm_controller_tb_simple__DOT__dut__DOT__best_priority 
                        = (7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[1U] 
                                 >> 0xcU));
                    hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                        = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0U] 
                                    >> 4U));
                } else if (((7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[1U] 
                                   >> 0xcU)) == (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_priority))) {
                    if (((0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0U] 
                                   >> 4U)) < (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_age))) {
                        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0U;
                        hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                            = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0U] 
                                        >> 4U));
                    }
                }
            }
        } else {
            vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0U;
            hbm_controller_tb_simple__DOT__dut__DOT__best_priority 
                = (7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[1U] 
                         >> 0xcU));
            hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0U] 
                            >> 4U));
            vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit 
                = hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit;
            vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__grant_valid = 1U;
        }
    }
    hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit = 0U;
    if (((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[8U] 
          >> 9U) & (0U == (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__state)))) {
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
            = (0xfffffffffULL & (((QData)((IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[7U])) 
                                  << 0x1bU) | ((QData)((IData)(
                                                               vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[6U])) 
                                               >> 5U)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch 
            = (0x1fU & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                                >> 0x1eU)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bg 
            = (7U & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                             >> 0x1aU)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_pch 
            = (1U & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                             >> 0x17U)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bank 
            = (0xfU & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                               >> 0x16U)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_row 
            = (0xffffU & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                                  >> 6U)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__Vfuncout 
            = (((((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__row_open 
                   >> ([&]() {
                                    vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__ch 
                                        = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                    vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__Vfuncout 
                                        = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__ch;
                                }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__Vfuncout))) 
                  & ((IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_pch) 
                     == (1U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_pch_reg 
                               >> ([&]() {
                                            vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__ch 
                                                = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                            vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__Vfuncout 
                                                = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__ch;
                                        }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__Vfuncout)))))) 
                 & ((IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bg) 
                    == ((0x5fU >= (0x7fU & ((IData)(3U) 
                                            * VL_EXTEND_II(32,5, 
                                                           ([&]() {
                                                    vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__ch 
                                                        = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                                    vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__Vfuncout 
                                                        = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__ch;
                                                }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__Vfuncout))))))
                         ? (7U & VL_SEL_IWII(96, vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_bg_reg, 
                                             (0x7fU 
                                              & ((IData)(3U) 
                                                 * 
                                                 VL_EXTEND_II(32,5, 
                                                              ([&]() {
                                                        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__ch 
                                                            = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                                        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__Vfuncout 
                                                            = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__ch;
                                                    }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__Vfuncout))))), 3U))
                         : 0U))) & ((IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bank) 
                                    == (0xfU & VL_SEL_IWII(128, vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_bank_reg, 
                                                           (0x7fU 
                                                            & VL_SHIFTL_III(7,32,32, 
                                                                            VL_EXTEND_II(32,5, 
                                                                                ([&]() {
                                                vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__ch 
                                                    = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                                vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__Vfuncout 
                                                    = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__ch;
                                            }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__Vfuncout))), 2U)), 4U)))) 
               & ((IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_row) 
                  == (0xffffU & VL_SEL_IWII(512, vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_row_reg, 
                                            (0x1ffU 
                                             & VL_SHIFTL_III(9,32,32, 
                                                             VL_EXTEND_II(32,5, 
                                                                          ([&]() {
                                            vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__ch 
                                                = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                            vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__Vfuncout 
                                                = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__ch;
                                        }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__Vfuncout))), 4U)), 0x10U))));
        hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit 
            = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__Vfuncout;
        if (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__grant_valid) {
            if (((IData)(hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit) 
                 & (~ (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit)))) {
                vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 1U;
                hbm_controller_tb_simple__DOT__dut__DOT__best_priority 
                    = (7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[5U] 
                             >> 0x11U));
                hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                    = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[4U] 
                                >> 9U));
                vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit 
                    = hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit;
            } else if (((IData)(hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit) 
                        & (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit))) {
                if (((7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[5U] 
                            >> 0x11U)) > (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_priority))) {
                    vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 1U;
                    hbm_controller_tb_simple__DOT__dut__DOT__best_priority 
                        = (7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[5U] 
                                 >> 0x11U));
                    hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                        = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[4U] 
                                    >> 9U));
                } else if (((7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[5U] 
                                   >> 0x11U)) == (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_priority))) {
                    if (((0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[4U] 
                                   >> 9U)) < (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_age))) {
                        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 1U;
                        hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                            = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[4U] 
                                        >> 9U));
                    }
                }
            } else if ((1U & ((~ (IData)(hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit)) 
                              & (~ (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit))))) {
                if (((7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[5U] 
                            >> 0x11U)) > (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_priority))) {
                    vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 1U;
                    hbm_controller_tb_simple__DOT__dut__DOT__best_priority 
                        = (7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[5U] 
                                 >> 0x11U));
                    hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                        = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[4U] 
                                    >> 9U));
                } else if (((7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[5U] 
                                   >> 0x11U)) == (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_priority))) {
                    if (((0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[4U] 
                                   >> 9U)) < (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_age))) {
                        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 1U;
                        hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                            = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[4U] 
                                        >> 9U));
                    }
                }
            }
        } else {
            vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 1U;
            hbm_controller_tb_simple__DOT__dut__DOT__best_priority 
                = (7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[5U] 
                         >> 0x11U));
            hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[4U] 
                            >> 9U));
            vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit 
                = hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit;
            vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__grant_valid = 1U;
        }
    }
    hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit = 0U;
    if (((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0xcU] 
          >> 0xeU) & (0U == (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__state)))) {
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
            = (0xfffffffffULL & (((QData)((IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0xbU])) 
                                  << 0x16U) | ((QData)((IData)(
                                                               vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0xaU])) 
                                               >> 0xaU)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch 
            = (0x1fU & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                                >> 0x1eU)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bg 
            = (7U & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                             >> 0x1aU)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_pch 
            = (1U & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                             >> 0x17U)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bank 
            = (0xfU & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                               >> 0x16U)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_row 
            = (0xffffU & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                                  >> 6U)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__Vfuncout 
            = (((((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__row_open 
                   >> ([&]() {
                                    vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__ch 
                                        = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                    vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__Vfuncout 
                                        = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__ch;
                                }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__Vfuncout))) 
                  & ((IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_pch) 
                     == (1U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_pch_reg 
                               >> ([&]() {
                                            vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__ch 
                                                = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                            vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__Vfuncout 
                                                = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__ch;
                                        }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__Vfuncout)))))) 
                 & ((IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bg) 
                    == ((0x5fU >= (0x7fU & ((IData)(3U) 
                                            * VL_EXTEND_II(32,5, 
                                                           ([&]() {
                                                    vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__ch 
                                                        = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                                    vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__Vfuncout 
                                                        = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__ch;
                                                }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__Vfuncout))))))
                         ? (7U & VL_SEL_IWII(96, vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_bg_reg, 
                                             (0x7fU 
                                              & ((IData)(3U) 
                                                 * 
                                                 VL_EXTEND_II(32,5, 
                                                              ([&]() {
                                                        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__ch 
                                                            = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                                        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__Vfuncout 
                                                            = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__ch;
                                                    }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__Vfuncout))))), 3U))
                         : 0U))) & ((IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bank) 
                                    == (0xfU & VL_SEL_IWII(128, vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_bank_reg, 
                                                           (0x7fU 
                                                            & VL_SHIFTL_III(7,32,32, 
                                                                            VL_EXTEND_II(32,5, 
                                                                                ([&]() {
                                                vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__ch 
                                                    = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                                vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__Vfuncout 
                                                    = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__ch;
                                            }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__Vfuncout))), 2U)), 4U)))) 
               & ((IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_row) 
                  == (0xffffU & VL_SEL_IWII(512, vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_row_reg, 
                                            (0x1ffU 
                                             & VL_SHIFTL_III(9,32,32, 
                                                             VL_EXTEND_II(32,5, 
                                                                          ([&]() {
                                            vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__ch 
                                                = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                            vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__Vfuncout 
                                                = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__ch;
                                        }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__Vfuncout))), 4U)), 0x10U))));
        hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit 
            = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__Vfuncout;
        if (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__grant_valid) {
            if (((IData)(hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit) 
                 & (~ (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit)))) {
                vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 2U;
                hbm_controller_tb_simple__DOT__dut__DOT__best_priority 
                    = (7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[9U] 
                             >> 0x16U));
                hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                    = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[8U] 
                                >> 0xeU));
                vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit 
                    = hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit;
            } else if (((IData)(hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit) 
                        & (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit))) {
                if (((7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[9U] 
                            >> 0x16U)) > (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_priority))) {
                    vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 2U;
                    hbm_controller_tb_simple__DOT__dut__DOT__best_priority 
                        = (7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[9U] 
                                 >> 0x16U));
                    hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                        = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[8U] 
                                    >> 0xeU));
                } else if (((7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[9U] 
                                   >> 0x16U)) == (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_priority))) {
                    if (((0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[8U] 
                                   >> 0xeU)) < (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_age))) {
                        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 2U;
                        hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                            = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[8U] 
                                        >> 0xeU));
                    }
                }
            } else if ((1U & ((~ (IData)(hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit)) 
                              & (~ (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit))))) {
                if (((7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[9U] 
                            >> 0x16U)) > (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_priority))) {
                    vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 2U;
                    hbm_controller_tb_simple__DOT__dut__DOT__best_priority 
                        = (7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[9U] 
                                 >> 0x16U));
                    hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                        = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[8U] 
                                    >> 0xeU));
                } else if (((7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[9U] 
                                   >> 0x16U)) == (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_priority))) {
                    if (((0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[8U] 
                                   >> 0xeU)) < (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_age))) {
                        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 2U;
                        hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                            = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[8U] 
                                        >> 0xeU));
                    }
                }
            }
        } else {
            vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 2U;
            hbm_controller_tb_simple__DOT__dut__DOT__best_priority 
                = (7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[9U] 
                         >> 0x16U));
            hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[8U] 
                            >> 0xeU));
            vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit 
                = hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit;
            vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__grant_valid = 1U;
        }
    }
    hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit = 0U;
    if (((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x10U] 
          >> 0x13U) & (0U == (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__state)))) {
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
            = (0xfffffffffULL & (((QData)((IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0xfU])) 
                                  << 0x11U) | ((QData)((IData)(
                                                               vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0xeU])) 
                                               >> 0xfU)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch 
            = (0x1fU & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                                >> 0x1eU)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bg 
            = (7U & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                             >> 0x1aU)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_pch 
            = (1U & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                             >> 0x17U)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bank 
            = (0xfU & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                               >> 0x16U)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_row 
            = (0xffffU & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                                  >> 6U)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__Vfuncout 
            = (((((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__row_open 
                   >> ([&]() {
                                    vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__ch 
                                        = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                    vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__Vfuncout 
                                        = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__ch;
                                }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__Vfuncout))) 
                  & ((IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_pch) 
                     == (1U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_pch_reg 
                               >> ([&]() {
                                            vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__ch 
                                                = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                            vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__Vfuncout 
                                                = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__ch;
                                        }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__Vfuncout)))))) 
                 & ((IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bg) 
                    == ((0x5fU >= (0x7fU & ((IData)(3U) 
                                            * VL_EXTEND_II(32,5, 
                                                           ([&]() {
                                                    vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__ch 
                                                        = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                                    vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__Vfuncout 
                                                        = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__ch;
                                                }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__Vfuncout))))))
                         ? (7U & VL_SEL_IWII(96, vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_bg_reg, 
                                             (0x7fU 
                                              & ((IData)(3U) 
                                                 * 
                                                 VL_EXTEND_II(32,5, 
                                                              ([&]() {
                                                        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__ch 
                                                            = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                                        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__Vfuncout 
                                                            = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__ch;
                                                    }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__Vfuncout))))), 3U))
                         : 0U))) & ((IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bank) 
                                    == (0xfU & VL_SEL_IWII(128, vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_bank_reg, 
                                                           (0x7fU 
                                                            & VL_SHIFTL_III(7,32,32, 
                                                                            VL_EXTEND_II(32,5, 
                                                                                ([&]() {
                                                vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__ch 
                                                    = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                                vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__Vfuncout 
                                                    = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__ch;
                                            }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__Vfuncout))), 2U)), 4U)))) 
               & ((IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_row) 
                  == (0xffffU & VL_SEL_IWII(512, vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_row_reg, 
                                            (0x1ffU 
                                             & VL_SHIFTL_III(9,32,32, 
                                                             VL_EXTEND_II(32,5, 
                                                                          ([&]() {
                                            vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__ch 
                                                = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                            vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__Vfuncout 
                                                = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__ch;
                                        }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__Vfuncout))), 4U)), 0x10U))));
        hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit 
            = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__Vfuncout;
        if (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__grant_valid) {
            if (((IData)(hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit) 
                 & (~ (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit)))) {
                vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 3U;
                hbm_controller_tb_simple__DOT__dut__DOT__best_priority 
                    = (7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0xdU] 
                             >> 0x1bU));
                hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                    = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0xcU] 
                                >> 0x13U));
                vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit 
                    = hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit;
            } else if (((IData)(hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit) 
                        & (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit))) {
                if (((7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0xdU] 
                            >> 0x1bU)) > (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_priority))) {
                    vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 3U;
                    hbm_controller_tb_simple__DOT__dut__DOT__best_priority 
                        = (7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0xdU] 
                                 >> 0x1bU));
                    hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                        = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0xcU] 
                                    >> 0x13U));
                } else if (((7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0xdU] 
                                   >> 0x1bU)) == (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_priority))) {
                    if (((0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0xcU] 
                                   >> 0x13U)) < (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_age))) {
                        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 3U;
                        hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                            = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0xcU] 
                                        >> 0x13U));
                    }
                }
            } else if ((1U & ((~ (IData)(hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit)) 
                              & (~ (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit))))) {
                if (((7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0xdU] 
                            >> 0x1bU)) > (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_priority))) {
                    vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 3U;
                    hbm_controller_tb_simple__DOT__dut__DOT__best_priority 
                        = (7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0xdU] 
                                 >> 0x1bU));
                    hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                        = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0xcU] 
                                    >> 0x13U));
                } else if (((7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0xdU] 
                                   >> 0x1bU)) == (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_priority))) {
                    if (((0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0xcU] 
                                   >> 0x13U)) < (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_age))) {
                        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 3U;
                        hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                            = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0xcU] 
                                        >> 0x13U));
                    }
                }
            }
        } else {
            vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 3U;
            hbm_controller_tb_simple__DOT__dut__DOT__best_priority 
                = (7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0xdU] 
                         >> 0x1bU));
            hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0xcU] 
                            >> 0x13U));
            vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit 
                = hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit;
            vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__grant_valid = 1U;
        }
    }
    hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit = 0U;
    if (((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x14U] 
          >> 0x18U) & (0U == (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__state)))) {
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
            = (0xfffffffffULL & (((QData)((IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x13U])) 
                                  << 0xcU) | ((QData)((IData)(
                                                              vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x12U])) 
                                              >> 0x14U)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch 
            = (0x1fU & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                                >> 0x1eU)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bg 
            = (7U & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                             >> 0x1aU)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_pch 
            = (1U & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                             >> 0x17U)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bank 
            = (0xfU & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                               >> 0x16U)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_row 
            = (0xffffU & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                                  >> 6U)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__Vfuncout 
            = (((((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__row_open 
                   >> ([&]() {
                                    vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__ch 
                                        = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                    vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__Vfuncout 
                                        = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__ch;
                                }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__Vfuncout))) 
                  & ((IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_pch) 
                     == (1U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_pch_reg 
                               >> ([&]() {
                                            vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__ch 
                                                = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                            vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__Vfuncout 
                                                = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__ch;
                                        }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__Vfuncout)))))) 
                 & ((IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bg) 
                    == ((0x5fU >= (0x7fU & ((IData)(3U) 
                                            * VL_EXTEND_II(32,5, 
                                                           ([&]() {
                                                    vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__ch 
                                                        = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                                    vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__Vfuncout 
                                                        = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__ch;
                                                }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__Vfuncout))))))
                         ? (7U & VL_SEL_IWII(96, vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_bg_reg, 
                                             (0x7fU 
                                              & ((IData)(3U) 
                                                 * 
                                                 VL_EXTEND_II(32,5, 
                                                              ([&]() {
                                                        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__ch 
                                                            = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                                        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__Vfuncout 
                                                            = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__ch;
                                                    }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__Vfuncout))))), 3U))
                         : 0U))) & ((IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bank) 
                                    == (0xfU & VL_SEL_IWII(128, vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_bank_reg, 
                                                           (0x7fU 
                                                            & VL_SHIFTL_III(7,32,32, 
                                                                            VL_EXTEND_II(32,5, 
                                                                                ([&]() {
                                                vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__ch 
                                                    = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                                vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__Vfuncout 
                                                    = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__ch;
                                            }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__Vfuncout))), 2U)), 4U)))) 
               & ((IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_row) 
                  == (0xffffU & VL_SEL_IWII(512, vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_row_reg, 
                                            (0x1ffU 
                                             & VL_SHIFTL_III(9,32,32, 
                                                             VL_EXTEND_II(32,5, 
                                                                          ([&]() {
                                            vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__ch 
                                                = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                            vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__Vfuncout 
                                                = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__ch;
                                        }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__Vfuncout))), 4U)), 0x10U))));
        hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit 
            = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__Vfuncout;
        if (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__grant_valid) {
            if (((IData)(hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit) 
                 & (~ (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit)))) {
                vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 4U;
                hbm_controller_tb_simple__DOT__dut__DOT__best_priority 
                    = (7U & vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x12U]);
                hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                    = (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x10U] 
                       >> 0x18U);
                vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit 
                    = hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit;
            } else if (((IData)(hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit) 
                        & (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit))) {
                if (((7U & vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x12U]) 
                     > (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_priority))) {
                    vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 4U;
                    hbm_controller_tb_simple__DOT__dut__DOT__best_priority 
                        = (7U & vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x12U]);
                    hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                        = (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x10U] 
                           >> 0x18U);
                } else if (((7U & vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x12U]) 
                            == (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_priority))) {
                    if (((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x10U] 
                          >> 0x18U) < (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_age))) {
                        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 4U;
                        hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                            = (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x10U] 
                               >> 0x18U);
                    }
                }
            } else if ((1U & ((~ (IData)(hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit)) 
                              & (~ (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit))))) {
                if (((7U & vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x12U]) 
                     > (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_priority))) {
                    vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 4U;
                    hbm_controller_tb_simple__DOT__dut__DOT__best_priority 
                        = (7U & vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x12U]);
                    hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                        = (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x10U] 
                           >> 0x18U);
                } else if (((7U & vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x12U]) 
                            == (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_priority))) {
                    if (((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x10U] 
                          >> 0x18U) < (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_age))) {
                        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 4U;
                        hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                            = (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x10U] 
                               >> 0x18U);
                    }
                }
            }
        } else {
            vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 4U;
            hbm_controller_tb_simple__DOT__dut__DOT__best_priority 
                = (7U & vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x12U]);
            hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                = (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x10U] 
                   >> 0x18U);
            vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit 
                = hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit;
            vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__grant_valid = 1U;
        }
    }
    hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit = 0U;
    if (((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x18U] 
          >> 0x1dU) & (0U == (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__state)))) {
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
            = (0xfffffffffULL & (((QData)((IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x17U])) 
                                  << 7U) | ((QData)((IData)(
                                                            vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x16U])) 
                                            >> 0x19U)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch 
            = (0x1fU & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                                >> 0x1eU)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bg 
            = (7U & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                             >> 0x1aU)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_pch 
            = (1U & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                             >> 0x17U)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bank 
            = (0xfU & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                               >> 0x16U)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_row 
            = (0xffffU & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                                  >> 6U)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__Vfuncout 
            = (((((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__row_open 
                   >> ([&]() {
                                    vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__ch 
                                        = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                    vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__Vfuncout 
                                        = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__ch;
                                }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__Vfuncout))) 
                  & ((IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_pch) 
                     == (1U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_pch_reg 
                               >> ([&]() {
                                            vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__ch 
                                                = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                            vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__Vfuncout 
                                                = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__ch;
                                        }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__Vfuncout)))))) 
                 & ((IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bg) 
                    == ((0x5fU >= (0x7fU & ((IData)(3U) 
                                            * VL_EXTEND_II(32,5, 
                                                           ([&]() {
                                                    vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__ch 
                                                        = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                                    vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__Vfuncout 
                                                        = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__ch;
                                                }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__Vfuncout))))))
                         ? (7U & VL_SEL_IWII(96, vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_bg_reg, 
                                             (0x7fU 
                                              & ((IData)(3U) 
                                                 * 
                                                 VL_EXTEND_II(32,5, 
                                                              ([&]() {
                                                        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__ch 
                                                            = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                                        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__Vfuncout 
                                                            = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__ch;
                                                    }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__Vfuncout))))), 3U))
                         : 0U))) & ((IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bank) 
                                    == (0xfU & VL_SEL_IWII(128, vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_bank_reg, 
                                                           (0x7fU 
                                                            & VL_SHIFTL_III(7,32,32, 
                                                                            VL_EXTEND_II(32,5, 
                                                                                ([&]() {
                                                vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__ch 
                                                    = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                                vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__Vfuncout 
                                                    = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__ch;
                                            }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__Vfuncout))), 2U)), 4U)))) 
               & ((IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_row) 
                  == (0xffffU & VL_SEL_IWII(512, vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_row_reg, 
                                            (0x1ffU 
                                             & VL_SHIFTL_III(9,32,32, 
                                                             VL_EXTEND_II(32,5, 
                                                                          ([&]() {
                                            vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__ch 
                                                = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                            vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__Vfuncout 
                                                = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__ch;
                                        }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__Vfuncout))), 4U)), 0x10U))));
        hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit 
            = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__Vfuncout;
        if (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__grant_valid) {
            if (((IData)(hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit) 
                 & (~ (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit)))) {
                vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 5U;
                hbm_controller_tb_simple__DOT__dut__DOT__best_priority 
                    = (7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x16U] 
                             >> 5U));
                hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                    = (0xffU & ((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x15U] 
                                 << 3U) | (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x14U] 
                                           >> 0x1dU)));
                vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit 
                    = hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit;
            } else if (((IData)(hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit) 
                        & (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit))) {
                if (((7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x16U] 
                            >> 5U)) > (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_priority))) {
                    vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 5U;
                    hbm_controller_tb_simple__DOT__dut__DOT__best_priority 
                        = (7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x16U] 
                                 >> 5U));
                    hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                        = (0xffU & ((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x15U] 
                                     << 3U) | (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x14U] 
                                               >> 0x1dU)));
                } else if (((7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x16U] 
                                   >> 5U)) == (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_priority))) {
                    if (((0xffU & ((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x15U] 
                                    << 3U) | (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x14U] 
                                              >> 0x1dU))) 
                         < (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_age))) {
                        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 5U;
                        hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                            = (0xffU & ((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x15U] 
                                         << 3U) | (
                                                   vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x14U] 
                                                   >> 0x1dU)));
                    }
                }
            } else if ((1U & ((~ (IData)(hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit)) 
                              & (~ (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit))))) {
                if (((7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x16U] 
                            >> 5U)) > (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_priority))) {
                    vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 5U;
                    hbm_controller_tb_simple__DOT__dut__DOT__best_priority 
                        = (7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x16U] 
                                 >> 5U));
                    hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                        = (0xffU & ((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x15U] 
                                     << 3U) | (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x14U] 
                                               >> 0x1dU)));
                } else if (((7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x16U] 
                                   >> 5U)) == (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_priority))) {
                    if (((0xffU & ((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x15U] 
                                    << 3U) | (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x14U] 
                                              >> 0x1dU))) 
                         < (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_age))) {
                        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 5U;
                        hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                            = (0xffU & ((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x15U] 
                                         << 3U) | (
                                                   vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x14U] 
                                                   >> 0x1dU)));
                    }
                }
            }
        } else {
            vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 5U;
            hbm_controller_tb_simple__DOT__dut__DOT__best_priority 
                = (7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x16U] 
                         >> 5U));
            hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                = (0xffU & ((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x15U] 
                             << 3U) | (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x14U] 
                                       >> 0x1dU)));
            vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit 
                = hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit;
            vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__grant_valid = 1U;
        }
    }
    hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit = 0U;
    if (((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x1dU] 
          >> 2U) & (0U == (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__state)))) {
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
            = (0xfffffffffULL & (((QData)((IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x1cU])) 
                                  << 0x22U) | (((QData)((IData)(
                                                                vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x1bU])) 
                                                << 2U) 
                                               | ((QData)((IData)(
                                                                  vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x1aU])) 
                                                  >> 0x1eU))));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch 
            = (0x1fU & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                                >> 0x1eU)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bg 
            = (7U & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                             >> 0x1aU)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_pch 
            = (1U & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                             >> 0x17U)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bank 
            = (0xfU & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                               >> 0x16U)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_row 
            = (0xffffU & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                                  >> 6U)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__Vfuncout 
            = (((((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__row_open 
                   >> ([&]() {
                                    vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__ch 
                                        = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                    vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__Vfuncout 
                                        = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__ch;
                                }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__Vfuncout))) 
                  & ((IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_pch) 
                     == (1U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_pch_reg 
                               >> ([&]() {
                                            vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__ch 
                                                = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                            vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__Vfuncout 
                                                = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__ch;
                                        }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__Vfuncout)))))) 
                 & ((IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bg) 
                    == ((0x5fU >= (0x7fU & ((IData)(3U) 
                                            * VL_EXTEND_II(32,5, 
                                                           ([&]() {
                                                    vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__ch 
                                                        = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                                    vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__Vfuncout 
                                                        = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__ch;
                                                }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__Vfuncout))))))
                         ? (7U & VL_SEL_IWII(96, vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_bg_reg, 
                                             (0x7fU 
                                              & ((IData)(3U) 
                                                 * 
                                                 VL_EXTEND_II(32,5, 
                                                              ([&]() {
                                                        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__ch 
                                                            = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                                        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__Vfuncout 
                                                            = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__ch;
                                                    }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__Vfuncout))))), 3U))
                         : 0U))) & ((IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bank) 
                                    == (0xfU & VL_SEL_IWII(128, vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_bank_reg, 
                                                           (0x7fU 
                                                            & VL_SHIFTL_III(7,32,32, 
                                                                            VL_EXTEND_II(32,5, 
                                                                                ([&]() {
                                                vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__ch 
                                                    = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                                vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__Vfuncout 
                                                    = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__ch;
                                            }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__Vfuncout))), 2U)), 4U)))) 
               & ((IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_row) 
                  == (0xffffU & VL_SEL_IWII(512, vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_row_reg, 
                                            (0x1ffU 
                                             & VL_SHIFTL_III(9,32,32, 
                                                             VL_EXTEND_II(32,5, 
                                                                          ([&]() {
                                            vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__ch 
                                                = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                            vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__Vfuncout 
                                                = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__ch;
                                        }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__Vfuncout))), 4U)), 0x10U))));
        hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit 
            = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__Vfuncout;
        if (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__grant_valid) {
            if (((IData)(hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit) 
                 & (~ (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit)))) {
                vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 6U;
                hbm_controller_tb_simple__DOT__dut__DOT__best_priority 
                    = (7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x1aU] 
                             >> 0xaU));
                hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                    = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x19U] 
                                >> 2U));
                vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit 
                    = hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit;
            } else if (((IData)(hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit) 
                        & (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit))) {
                if (((7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x1aU] 
                            >> 0xaU)) > (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_priority))) {
                    vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 6U;
                    hbm_controller_tb_simple__DOT__dut__DOT__best_priority 
                        = (7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x1aU] 
                                 >> 0xaU));
                    hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                        = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x19U] 
                                    >> 2U));
                } else if (((7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x1aU] 
                                   >> 0xaU)) == (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_priority))) {
                    if (((0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x19U] 
                                   >> 2U)) < (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_age))) {
                        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 6U;
                        hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                            = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x19U] 
                                        >> 2U));
                    }
                }
            } else if ((1U & ((~ (IData)(hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit)) 
                              & (~ (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit))))) {
                if (((7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x1aU] 
                            >> 0xaU)) > (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_priority))) {
                    vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 6U;
                    hbm_controller_tb_simple__DOT__dut__DOT__best_priority 
                        = (7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x1aU] 
                                 >> 0xaU));
                    hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                        = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x19U] 
                                    >> 2U));
                } else if (((7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x1aU] 
                                   >> 0xaU)) == (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_priority))) {
                    if (((0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x19U] 
                                   >> 2U)) < (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_age))) {
                        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 6U;
                        hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                            = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x19U] 
                                        >> 2U));
                    }
                }
            }
        } else {
            vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 6U;
            hbm_controller_tb_simple__DOT__dut__DOT__best_priority 
                = (7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x1aU] 
                         >> 0xaU));
            hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x19U] 
                            >> 2U));
            vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit 
                = hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit;
            vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__grant_valid = 1U;
        }
    }
    hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit = 0U;
    if (((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x21U] 
          >> 7U) & (0U == (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__state)))) {
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
            = (0xfffffffffULL & (((QData)((IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x20U])) 
                                  << 0x1dU) | ((QData)((IData)(
                                                               vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x1fU])) 
                                               >> 3U)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch 
            = (0x1fU & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                                >> 0x1eU)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bg 
            = (7U & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                             >> 0x1aU)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_pch 
            = (1U & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                             >> 0x17U)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bank 
            = (0xfU & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                               >> 0x16U)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_row 
            = (0xffffU & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                                  >> 6U)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__Vfuncout 
            = (((((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__row_open 
                   >> ([&]() {
                                    vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__ch 
                                        = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                    vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__Vfuncout 
                                        = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__ch;
                                }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__Vfuncout))) 
                  & ((IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_pch) 
                     == (1U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_pch_reg 
                               >> ([&]() {
                                            vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__ch 
                                                = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                            vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__Vfuncout 
                                                = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__ch;
                                        }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__Vfuncout)))))) 
                 & ((IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bg) 
                    == ((0x5fU >= (0x7fU & ((IData)(3U) 
                                            * VL_EXTEND_II(32,5, 
                                                           ([&]() {
                                                    vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__ch 
                                                        = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                                    vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__Vfuncout 
                                                        = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__ch;
                                                }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__Vfuncout))))))
                         ? (7U & VL_SEL_IWII(96, vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_bg_reg, 
                                             (0x7fU 
                                              & ((IData)(3U) 
                                                 * 
                                                 VL_EXTEND_II(32,5, 
                                                              ([&]() {
                                                        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__ch 
                                                            = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                                        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__Vfuncout 
                                                            = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__ch;
                                                    }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__Vfuncout))))), 3U))
                         : 0U))) & ((IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bank) 
                                    == (0xfU & VL_SEL_IWII(128, vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_bank_reg, 
                                                           (0x7fU 
                                                            & VL_SHIFTL_III(7,32,32, 
                                                                            VL_EXTEND_II(32,5, 
                                                                                ([&]() {
                                                vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__ch 
                                                    = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                                vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__Vfuncout 
                                                    = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__ch;
                                            }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__Vfuncout))), 2U)), 4U)))) 
               & ((IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_row) 
                  == (0xffffU & VL_SEL_IWII(512, vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_row_reg, 
                                            (0x1ffU 
                                             & VL_SHIFTL_III(9,32,32, 
                                                             VL_EXTEND_II(32,5, 
                                                                          ([&]() {
                                            vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__ch 
                                                = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                            vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__Vfuncout 
                                                = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__ch;
                                        }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__Vfuncout))), 4U)), 0x10U))));
        hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit 
            = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__Vfuncout;
        if (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__grant_valid) {
            if (((IData)(hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit) 
                 & (~ (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit)))) {
                vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 7U;
                hbm_controller_tb_simple__DOT__dut__DOT__best_priority 
                    = (7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x1eU] 
                             >> 0xfU));
                hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                    = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x1dU] 
                                >> 7U));
                vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit 
                    = hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit;
            } else if (((IData)(hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit) 
                        & (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit))) {
                if (((7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x1eU] 
                            >> 0xfU)) > (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_priority))) {
                    vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 7U;
                    hbm_controller_tb_simple__DOT__dut__DOT__best_priority 
                        = (7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x1eU] 
                                 >> 0xfU));
                    hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                        = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x1dU] 
                                    >> 7U));
                } else if (((7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x1eU] 
                                   >> 0xfU)) == (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_priority))) {
                    if (((0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x1dU] 
                                   >> 7U)) < (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_age))) {
                        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 7U;
                        hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                            = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x1dU] 
                                        >> 7U));
                    }
                }
            } else if ((1U & ((~ (IData)(hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit)) 
                              & (~ (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit))))) {
                if (((7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x1eU] 
                            >> 0xfU)) > (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_priority))) {
                    vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 7U;
                    hbm_controller_tb_simple__DOT__dut__DOT__best_priority 
                        = (7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x1eU] 
                                 >> 0xfU));
                    hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                        = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x1dU] 
                                    >> 7U));
                } else if (((7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x1eU] 
                                   >> 0xfU)) == (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_priority))) {
                    if (((0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x1dU] 
                                   >> 7U)) < (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_age))) {
                        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 7U;
                        hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                            = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x1dU] 
                                        >> 7U));
                    }
                }
            }
        } else {
            vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 7U;
            hbm_controller_tb_simple__DOT__dut__DOT__best_priority 
                = (7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x1eU] 
                         >> 0xfU));
            hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x1dU] 
                            >> 7U));
            vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit 
                = hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit;
            vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__grant_valid = 1U;
        }
    }
    hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit = 0U;
    if (((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x25U] 
          >> 0xcU) & (0U == (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__state)))) {
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
            = (0xfffffffffULL & (((QData)((IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x24U])) 
                                  << 0x18U) | ((QData)((IData)(
                                                               vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x23U])) 
                                               >> 8U)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch 
            = (0x1fU & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                                >> 0x1eU)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bg 
            = (7U & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                             >> 0x1aU)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_pch 
            = (1U & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                             >> 0x17U)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bank 
            = (0xfU & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                               >> 0x16U)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_row 
            = (0xffffU & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                                  >> 6U)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__Vfuncout 
            = (((((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__row_open 
                   >> ([&]() {
                                    vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__ch 
                                        = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                    vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__Vfuncout 
                                        = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__ch;
                                }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__Vfuncout))) 
                  & ((IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_pch) 
                     == (1U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_pch_reg 
                               >> ([&]() {
                                            vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__ch 
                                                = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                            vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__Vfuncout 
                                                = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__ch;
                                        }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__Vfuncout)))))) 
                 & ((IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bg) 
                    == ((0x5fU >= (0x7fU & ((IData)(3U) 
                                            * VL_EXTEND_II(32,5, 
                                                           ([&]() {
                                                    vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__ch 
                                                        = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                                    vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__Vfuncout 
                                                        = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__ch;
                                                }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__Vfuncout))))))
                         ? (7U & VL_SEL_IWII(96, vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_bg_reg, 
                                             (0x7fU 
                                              & ((IData)(3U) 
                                                 * 
                                                 VL_EXTEND_II(32,5, 
                                                              ([&]() {
                                                        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__ch 
                                                            = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                                        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__Vfuncout 
                                                            = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__ch;
                                                    }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__Vfuncout))))), 3U))
                         : 0U))) & ((IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bank) 
                                    == (0xfU & VL_SEL_IWII(128, vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_bank_reg, 
                                                           (0x7fU 
                                                            & VL_SHIFTL_III(7,32,32, 
                                                                            VL_EXTEND_II(32,5, 
                                                                                ([&]() {
                                                vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__ch 
                                                    = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                                vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__Vfuncout 
                                                    = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__ch;
                                            }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__Vfuncout))), 2U)), 4U)))) 
               & ((IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_row) 
                  == (0xffffU & VL_SEL_IWII(512, vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_row_reg, 
                                            (0x1ffU 
                                             & VL_SHIFTL_III(9,32,32, 
                                                             VL_EXTEND_II(32,5, 
                                                                          ([&]() {
                                            vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__ch 
                                                = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                            vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__Vfuncout 
                                                = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__ch;
                                        }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__Vfuncout))), 4U)), 0x10U))));
        hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit 
            = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__Vfuncout;
        if (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__grant_valid) {
            if (((IData)(hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit) 
                 & (~ (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit)))) {
                vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 8U;
                hbm_controller_tb_simple__DOT__dut__DOT__best_priority 
                    = (7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x22U] 
                             >> 0x14U));
                hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                    = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x21U] 
                                >> 0xcU));
                vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit 
                    = hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit;
            } else if (((IData)(hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit) 
                        & (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit))) {
                if (((7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x22U] 
                            >> 0x14U)) > (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_priority))) {
                    vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 8U;
                    hbm_controller_tb_simple__DOT__dut__DOT__best_priority 
                        = (7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x22U] 
                                 >> 0x14U));
                    hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                        = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x21U] 
                                    >> 0xcU));
                } else if (((7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x22U] 
                                   >> 0x14U)) == (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_priority))) {
                    if (((0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x21U] 
                                   >> 0xcU)) < (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_age))) {
                        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 8U;
                        hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                            = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x21U] 
                                        >> 0xcU));
                    }
                }
            } else if ((1U & ((~ (IData)(hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit)) 
                              & (~ (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit))))) {
                if (((7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x22U] 
                            >> 0x14U)) > (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_priority))) {
                    vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 8U;
                    hbm_controller_tb_simple__DOT__dut__DOT__best_priority 
                        = (7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x22U] 
                                 >> 0x14U));
                    hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                        = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x21U] 
                                    >> 0xcU));
                } else if (((7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x22U] 
                                   >> 0x14U)) == (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_priority))) {
                    if (((0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x21U] 
                                   >> 0xcU)) < (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_age))) {
                        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 8U;
                        hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                            = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x21U] 
                                        >> 0xcU));
                    }
                }
            }
        } else {
            vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 8U;
            hbm_controller_tb_simple__DOT__dut__DOT__best_priority 
                = (7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x22U] 
                         >> 0x14U));
            hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x21U] 
                            >> 0xcU));
            vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit 
                = hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit;
            vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__grant_valid = 1U;
        }
    }
    hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit = 0U;
    if (((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x29U] 
          >> 0x11U) & (0U == (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__state)))) {
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
            = (0xfffffffffULL & (((QData)((IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x28U])) 
                                  << 0x13U) | ((QData)((IData)(
                                                               vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x27U])) 
                                               >> 0xdU)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch 
            = (0x1fU & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                                >> 0x1eU)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bg 
            = (7U & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                             >> 0x1aU)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_pch 
            = (1U & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                             >> 0x17U)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bank 
            = (0xfU & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                               >> 0x16U)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_row 
            = (0xffffU & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                                  >> 6U)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__Vfuncout 
            = (((((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__row_open 
                   >> ([&]() {
                                    vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__ch 
                                        = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                    vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__Vfuncout 
                                        = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__ch;
                                }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__Vfuncout))) 
                  & ((IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_pch) 
                     == (1U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_pch_reg 
                               >> ([&]() {
                                            vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__ch 
                                                = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                            vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__Vfuncout 
                                                = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__ch;
                                        }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__Vfuncout)))))) 
                 & ((IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bg) 
                    == ((0x5fU >= (0x7fU & ((IData)(3U) 
                                            * VL_EXTEND_II(32,5, 
                                                           ([&]() {
                                                    vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__ch 
                                                        = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                                    vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__Vfuncout 
                                                        = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__ch;
                                                }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__Vfuncout))))))
                         ? (7U & VL_SEL_IWII(96, vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_bg_reg, 
                                             (0x7fU 
                                              & ((IData)(3U) 
                                                 * 
                                                 VL_EXTEND_II(32,5, 
                                                              ([&]() {
                                                        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__ch 
                                                            = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                                        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__Vfuncout 
                                                            = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__ch;
                                                    }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__Vfuncout))))), 3U))
                         : 0U))) & ((IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bank) 
                                    == (0xfU & VL_SEL_IWII(128, vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_bank_reg, 
                                                           (0x7fU 
                                                            & VL_SHIFTL_III(7,32,32, 
                                                                            VL_EXTEND_II(32,5, 
                                                                                ([&]() {
                                                vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__ch 
                                                    = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                                vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__Vfuncout 
                                                    = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__ch;
                                            }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__Vfuncout))), 2U)), 4U)))) 
               & ((IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_row) 
                  == (0xffffU & VL_SEL_IWII(512, vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_row_reg, 
                                            (0x1ffU 
                                             & VL_SHIFTL_III(9,32,32, 
                                                             VL_EXTEND_II(32,5, 
                                                                          ([&]() {
                                            vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__ch 
                                                = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                            vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__Vfuncout 
                                                = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__ch;
                                        }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__Vfuncout))), 4U)), 0x10U))));
        hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit 
            = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__Vfuncout;
        if (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__grant_valid) {
            if (((IData)(hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit) 
                 & (~ (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit)))) {
                vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 9U;
                hbm_controller_tb_simple__DOT__dut__DOT__best_priority 
                    = (7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x26U] 
                             >> 0x19U));
                hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                    = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x25U] 
                                >> 0x11U));
                vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit 
                    = hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit;
            } else if (((IData)(hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit) 
                        & (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit))) {
                if (((7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x26U] 
                            >> 0x19U)) > (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_priority))) {
                    vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 9U;
                    hbm_controller_tb_simple__DOT__dut__DOT__best_priority 
                        = (7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x26U] 
                                 >> 0x19U));
                    hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                        = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x25U] 
                                    >> 0x11U));
                } else if (((7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x26U] 
                                   >> 0x19U)) == (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_priority))) {
                    if (((0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x25U] 
                                   >> 0x11U)) < (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_age))) {
                        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 9U;
                        hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                            = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x25U] 
                                        >> 0x11U));
                    }
                }
            } else if ((1U & ((~ (IData)(hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit)) 
                              & (~ (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit))))) {
                if (((7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x26U] 
                            >> 0x19U)) > (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_priority))) {
                    vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 9U;
                    hbm_controller_tb_simple__DOT__dut__DOT__best_priority 
                        = (7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x26U] 
                                 >> 0x19U));
                    hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                        = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x25U] 
                                    >> 0x11U));
                } else if (((7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x26U] 
                                   >> 0x19U)) == (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_priority))) {
                    if (((0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x25U] 
                                   >> 0x11U)) < (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_age))) {
                        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 9U;
                        hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                            = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x25U] 
                                        >> 0x11U));
                    }
                }
            }
        } else {
            vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 9U;
            hbm_controller_tb_simple__DOT__dut__DOT__best_priority 
                = (7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x26U] 
                         >> 0x19U));
            hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x25U] 
                            >> 0x11U));
            vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit 
                = hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit;
            vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__grant_valid = 1U;
        }
    }
    hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit = 0U;
    if (((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x2dU] 
          >> 0x16U) & (0U == (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__state)))) {
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
            = (0xfffffffffULL & (((QData)((IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x2cU])) 
                                  << 0xeU) | ((QData)((IData)(
                                                              vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x2bU])) 
                                              >> 0x12U)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch 
            = (0x1fU & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                                >> 0x1eU)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bg 
            = (7U & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                             >> 0x1aU)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_pch 
            = (1U & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                             >> 0x17U)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bank 
            = (0xfU & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                               >> 0x16U)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_row 
            = (0xffffU & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                                  >> 6U)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__Vfuncout 
            = (((((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__row_open 
                   >> ([&]() {
                                    vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__ch 
                                        = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                    vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__Vfuncout 
                                        = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__ch;
                                }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__Vfuncout))) 
                  & ((IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_pch) 
                     == (1U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_pch_reg 
                               >> ([&]() {
                                            vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__ch 
                                                = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                            vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__Vfuncout 
                                                = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__ch;
                                        }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__Vfuncout)))))) 
                 & ((IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bg) 
                    == ((0x5fU >= (0x7fU & ((IData)(3U) 
                                            * VL_EXTEND_II(32,5, 
                                                           ([&]() {
                                                    vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__ch 
                                                        = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                                    vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__Vfuncout 
                                                        = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__ch;
                                                }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__Vfuncout))))))
                         ? (7U & VL_SEL_IWII(96, vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_bg_reg, 
                                             (0x7fU 
                                              & ((IData)(3U) 
                                                 * 
                                                 VL_EXTEND_II(32,5, 
                                                              ([&]() {
                                                        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__ch 
                                                            = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                                        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__Vfuncout 
                                                            = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__ch;
                                                    }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__Vfuncout))))), 3U))
                         : 0U))) & ((IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bank) 
                                    == (0xfU & VL_SEL_IWII(128, vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_bank_reg, 
                                                           (0x7fU 
                                                            & VL_SHIFTL_III(7,32,32, 
                                                                            VL_EXTEND_II(32,5, 
                                                                                ([&]() {
                                                vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__ch 
                                                    = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                                vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__Vfuncout 
                                                    = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__ch;
                                            }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__Vfuncout))), 2U)), 4U)))) 
               & ((IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_row) 
                  == (0xffffU & VL_SEL_IWII(512, vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_row_reg, 
                                            (0x1ffU 
                                             & VL_SHIFTL_III(9,32,32, 
                                                             VL_EXTEND_II(32,5, 
                                                                          ([&]() {
                                            vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__ch 
                                                = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                            vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__Vfuncout 
                                                = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__ch;
                                        }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__Vfuncout))), 4U)), 0x10U))));
        hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit 
            = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__Vfuncout;
        if (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__grant_valid) {
            if (((IData)(hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit) 
                 & (~ (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit)))) {
                vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0xaU;
                hbm_controller_tb_simple__DOT__dut__DOT__best_priority 
                    = (7U & ((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x2bU] 
                              << 2U) | (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x2aU] 
                                        >> 0x1eU)));
                hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                    = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x29U] 
                                >> 0x16U));
                vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit 
                    = hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit;
            } else if (((IData)(hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit) 
                        & (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit))) {
                if (((7U & ((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x2bU] 
                             << 2U) | (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x2aU] 
                                       >> 0x1eU))) 
                     > (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_priority))) {
                    vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0xaU;
                    hbm_controller_tb_simple__DOT__dut__DOT__best_priority 
                        = (7U & ((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x2bU] 
                                  << 2U) | (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x2aU] 
                                            >> 0x1eU)));
                    hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                        = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x29U] 
                                    >> 0x16U));
                } else if (((7U & ((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x2bU] 
                                    << 2U) | (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x2aU] 
                                              >> 0x1eU))) 
                            == (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_priority))) {
                    if (((0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x29U] 
                                   >> 0x16U)) < (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_age))) {
                        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0xaU;
                        hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                            = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x29U] 
                                        >> 0x16U));
                    }
                }
            } else if ((1U & ((~ (IData)(hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit)) 
                              & (~ (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit))))) {
                if (((7U & ((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x2bU] 
                             << 2U) | (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x2aU] 
                                       >> 0x1eU))) 
                     > (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_priority))) {
                    vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0xaU;
                    hbm_controller_tb_simple__DOT__dut__DOT__best_priority 
                        = (7U & ((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x2bU] 
                                  << 2U) | (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x2aU] 
                                            >> 0x1eU)));
                    hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                        = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x29U] 
                                    >> 0x16U));
                } else if (((7U & ((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x2bU] 
                                    << 2U) | (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x2aU] 
                                              >> 0x1eU))) 
                            == (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_priority))) {
                    if (((0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x29U] 
                                   >> 0x16U)) < (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_age))) {
                        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0xaU;
                        hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                            = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x29U] 
                                        >> 0x16U));
                    }
                }
            }
        } else {
            vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0xaU;
            hbm_controller_tb_simple__DOT__dut__DOT__best_priority 
                = (7U & ((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x2bU] 
                          << 2U) | (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x2aU] 
                                    >> 0x1eU)));
            hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x29U] 
                            >> 0x16U));
            vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit 
                = hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit;
            vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__grant_valid = 1U;
        }
    }
    hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit = 0U;
    if (((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x31U] 
          >> 0x1bU) & (0U == (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__state)))) {
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
            = (0xfffffffffULL & (((QData)((IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x30U])) 
                                  << 9U) | ((QData)((IData)(
                                                            vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x2fU])) 
                                            >> 0x17U)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch 
            = (0x1fU & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                                >> 0x1eU)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bg 
            = (7U & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                             >> 0x1aU)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_pch 
            = (1U & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                             >> 0x17U)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bank 
            = (0xfU & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                               >> 0x16U)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_row 
            = (0xffffU & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                                  >> 6U)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__Vfuncout 
            = (((((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__row_open 
                   >> ([&]() {
                                    vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__ch 
                                        = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                    vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__Vfuncout 
                                        = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__ch;
                                }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__Vfuncout))) 
                  & ((IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_pch) 
                     == (1U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_pch_reg 
                               >> ([&]() {
                                            vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__ch 
                                                = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                            vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__Vfuncout 
                                                = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__ch;
                                        }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__Vfuncout)))))) 
                 & ((IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bg) 
                    == ((0x5fU >= (0x7fU & ((IData)(3U) 
                                            * VL_EXTEND_II(32,5, 
                                                           ([&]() {
                                                    vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__ch 
                                                        = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                                    vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__Vfuncout 
                                                        = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__ch;
                                                }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__Vfuncout))))))
                         ? (7U & VL_SEL_IWII(96, vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_bg_reg, 
                                             (0x7fU 
                                              & ((IData)(3U) 
                                                 * 
                                                 VL_EXTEND_II(32,5, 
                                                              ([&]() {
                                                        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__ch 
                                                            = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                                        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__Vfuncout 
                                                            = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__ch;
                                                    }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__Vfuncout))))), 3U))
                         : 0U))) & ((IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bank) 
                                    == (0xfU & VL_SEL_IWII(128, vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_bank_reg, 
                                                           (0x7fU 
                                                            & VL_SHIFTL_III(7,32,32, 
                                                                            VL_EXTEND_II(32,5, 
                                                                                ([&]() {
                                                vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__ch 
                                                    = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                                vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__Vfuncout 
                                                    = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__ch;
                                            }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__Vfuncout))), 2U)), 4U)))) 
               & ((IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_row) 
                  == (0xffffU & VL_SEL_IWII(512, vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_row_reg, 
                                            (0x1ffU 
                                             & VL_SHIFTL_III(9,32,32, 
                                                             VL_EXTEND_II(32,5, 
                                                                          ([&]() {
                                            vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__ch 
                                                = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                            vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__Vfuncout 
                                                = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__ch;
                                        }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__Vfuncout))), 4U)), 0x10U))));
        hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit 
            = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__Vfuncout;
        if (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__grant_valid) {
            if (((IData)(hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit) 
                 & (~ (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit)))) {
                vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0xbU;
                hbm_controller_tb_simple__DOT__dut__DOT__best_priority 
                    = (7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x2fU] 
                             >> 3U));
                hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                    = (0xffU & ((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x2eU] 
                                 << 5U) | (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x2dU] 
                                           >> 0x1bU)));
                vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit 
                    = hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit;
            } else if (((IData)(hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit) 
                        & (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit))) {
                if (((7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x2fU] 
                            >> 3U)) > (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_priority))) {
                    vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0xbU;
                    hbm_controller_tb_simple__DOT__dut__DOT__best_priority 
                        = (7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x2fU] 
                                 >> 3U));
                    hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                        = (0xffU & ((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x2eU] 
                                     << 5U) | (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x2dU] 
                                               >> 0x1bU)));
                } else if (((7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x2fU] 
                                   >> 3U)) == (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_priority))) {
                    if (((0xffU & ((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x2eU] 
                                    << 5U) | (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x2dU] 
                                              >> 0x1bU))) 
                         < (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_age))) {
                        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0xbU;
                        hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                            = (0xffU & ((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x2eU] 
                                         << 5U) | (
                                                   vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x2dU] 
                                                   >> 0x1bU)));
                    }
                }
            } else if ((1U & ((~ (IData)(hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit)) 
                              & (~ (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit))))) {
                if (((7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x2fU] 
                            >> 3U)) > (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_priority))) {
                    vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0xbU;
                    hbm_controller_tb_simple__DOT__dut__DOT__best_priority 
                        = (7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x2fU] 
                                 >> 3U));
                    hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                        = (0xffU & ((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x2eU] 
                                     << 5U) | (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x2dU] 
                                               >> 0x1bU)));
                } else if (((7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x2fU] 
                                   >> 3U)) == (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_priority))) {
                    if (((0xffU & ((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x2eU] 
                                    << 5U) | (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x2dU] 
                                              >> 0x1bU))) 
                         < (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_age))) {
                        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0xbU;
                        hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                            = (0xffU & ((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x2eU] 
                                         << 5U) | (
                                                   vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x2dU] 
                                                   >> 0x1bU)));
                    }
                }
            }
        } else {
            vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0xbU;
            hbm_controller_tb_simple__DOT__dut__DOT__best_priority 
                = (7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x2fU] 
                         >> 3U));
            hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                = (0xffU & ((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x2eU] 
                             << 5U) | (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x2dU] 
                                       >> 0x1bU)));
            vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit 
                = hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit;
            vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__grant_valid = 1U;
        }
    }
    hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit = 0U;
    if ((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x36U] 
         & (0U == (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__state)))) {
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
            = (0xfffffffffULL & (((QData)((IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x34U])) 
                                  << 4U) | ((QData)((IData)(
                                                            vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x33U])) 
                                            >> 0x1cU)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch 
            = (0x1fU & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                                >> 0x1eU)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bg 
            = (7U & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                             >> 0x1aU)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_pch 
            = (1U & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                             >> 0x17U)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bank 
            = (0xfU & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                               >> 0x16U)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_row 
            = (0xffffU & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                                  >> 6U)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__Vfuncout 
            = (((((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__row_open 
                   >> ([&]() {
                                    vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__ch 
                                        = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                    vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__Vfuncout 
                                        = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__ch;
                                }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__Vfuncout))) 
                  & ((IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_pch) 
                     == (1U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_pch_reg 
                               >> ([&]() {
                                            vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__ch 
                                                = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                            vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__Vfuncout 
                                                = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__ch;
                                        }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__Vfuncout)))))) 
                 & ((IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bg) 
                    == ((0x5fU >= (0x7fU & ((IData)(3U) 
                                            * VL_EXTEND_II(32,5, 
                                                           ([&]() {
                                                    vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__ch 
                                                        = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                                    vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__Vfuncout 
                                                        = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__ch;
                                                }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__Vfuncout))))))
                         ? (7U & VL_SEL_IWII(96, vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_bg_reg, 
                                             (0x7fU 
                                              & ((IData)(3U) 
                                                 * 
                                                 VL_EXTEND_II(32,5, 
                                                              ([&]() {
                                                        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__ch 
                                                            = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                                        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__Vfuncout 
                                                            = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__ch;
                                                    }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__Vfuncout))))), 3U))
                         : 0U))) & ((IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bank) 
                                    == (0xfU & VL_SEL_IWII(128, vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_bank_reg, 
                                                           (0x7fU 
                                                            & VL_SHIFTL_III(7,32,32, 
                                                                            VL_EXTEND_II(32,5, 
                                                                                ([&]() {
                                                vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__ch 
                                                    = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                                vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__Vfuncout 
                                                    = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__ch;
                                            }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__Vfuncout))), 2U)), 4U)))) 
               & ((IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_row) 
                  == (0xffffU & VL_SEL_IWII(512, vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_row_reg, 
                                            (0x1ffU 
                                             & VL_SHIFTL_III(9,32,32, 
                                                             VL_EXTEND_II(32,5, 
                                                                          ([&]() {
                                            vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__ch 
                                                = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                            vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__Vfuncout 
                                                = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__ch;
                                        }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__Vfuncout))), 4U)), 0x10U))));
        hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit 
            = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__Vfuncout;
        if (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__grant_valid) {
            if (((IData)(hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit) 
                 & (~ (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit)))) {
                vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0xcU;
                hbm_controller_tb_simple__DOT__dut__DOT__best_priority 
                    = (7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x33U] 
                             >> 8U));
                hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                    = (0xffU & vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x32U]);
                vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit 
                    = hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit;
            } else if (((IData)(hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit) 
                        & (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit))) {
                if (((7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x33U] 
                            >> 8U)) > (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_priority))) {
                    vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0xcU;
                    hbm_controller_tb_simple__DOT__dut__DOT__best_priority 
                        = (7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x33U] 
                                 >> 8U));
                    hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                        = (0xffU & vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x32U]);
                } else if (((7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x33U] 
                                   >> 8U)) == (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_priority))) {
                    if (((0xffU & vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x32U]) 
                         < (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_age))) {
                        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0xcU;
                        hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                            = (0xffU & vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x32U]);
                    }
                }
            } else if ((1U & ((~ (IData)(hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit)) 
                              & (~ (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit))))) {
                if (((7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x33U] 
                            >> 8U)) > (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_priority))) {
                    vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0xcU;
                    hbm_controller_tb_simple__DOT__dut__DOT__best_priority 
                        = (7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x33U] 
                                 >> 8U));
                    hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                        = (0xffU & vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x32U]);
                } else if (((7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x33U] 
                                   >> 8U)) == (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_priority))) {
                    if (((0xffU & vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x32U]) 
                         < (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_age))) {
                        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0xcU;
                        hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                            = (0xffU & vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x32U]);
                    }
                }
            }
        } else {
            vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0xcU;
            hbm_controller_tb_simple__DOT__dut__DOT__best_priority 
                = (7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x33U] 
                         >> 8U));
            hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                = (0xffU & vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x32U]);
            vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit 
                = hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit;
            vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__grant_valid = 1U;
        }
    }
    hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit = 0U;
    if (((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x3aU] 
          >> 5U) & (0U == (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__state)))) {
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
            = (0xfffffffffULL & (((QData)((IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x39U])) 
                                  << 0x1fU) | ((QData)((IData)(
                                                               vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x38U])) 
                                               >> 1U)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch 
            = (0x1fU & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                                >> 0x1eU)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bg 
            = (7U & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                             >> 0x1aU)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_pch 
            = (1U & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                             >> 0x17U)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bank 
            = (0xfU & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                               >> 0x16U)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_row 
            = (0xffffU & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                                  >> 6U)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__Vfuncout 
            = (((((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__row_open 
                   >> ([&]() {
                                    vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__ch 
                                        = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                    vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__Vfuncout 
                                        = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__ch;
                                }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__Vfuncout))) 
                  & ((IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_pch) 
                     == (1U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_pch_reg 
                               >> ([&]() {
                                            vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__ch 
                                                = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                            vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__Vfuncout 
                                                = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__ch;
                                        }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__Vfuncout)))))) 
                 & ((IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bg) 
                    == ((0x5fU >= (0x7fU & ((IData)(3U) 
                                            * VL_EXTEND_II(32,5, 
                                                           ([&]() {
                                                    vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__ch 
                                                        = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                                    vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__Vfuncout 
                                                        = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__ch;
                                                }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__Vfuncout))))))
                         ? (7U & VL_SEL_IWII(96, vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_bg_reg, 
                                             (0x7fU 
                                              & ((IData)(3U) 
                                                 * 
                                                 VL_EXTEND_II(32,5, 
                                                              ([&]() {
                                                        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__ch 
                                                            = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                                        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__Vfuncout 
                                                            = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__ch;
                                                    }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__Vfuncout))))), 3U))
                         : 0U))) & ((IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bank) 
                                    == (0xfU & VL_SEL_IWII(128, vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_bank_reg, 
                                                           (0x7fU 
                                                            & VL_SHIFTL_III(7,32,32, 
                                                                            VL_EXTEND_II(32,5, 
                                                                                ([&]() {
                                                vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__ch 
                                                    = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                                vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__Vfuncout 
                                                    = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__ch;
                                            }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__Vfuncout))), 2U)), 4U)))) 
               & ((IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_row) 
                  == (0xffffU & VL_SEL_IWII(512, vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_row_reg, 
                                            (0x1ffU 
                                             & VL_SHIFTL_III(9,32,32, 
                                                             VL_EXTEND_II(32,5, 
                                                                          ([&]() {
                                            vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__ch 
                                                = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                            vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__Vfuncout 
                                                = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__ch;
                                        }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__Vfuncout))), 4U)), 0x10U))));
        hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit 
            = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__Vfuncout;
        if (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__grant_valid) {
            if (((IData)(hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit) 
                 & (~ (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit)))) {
                vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0xdU;
                hbm_controller_tb_simple__DOT__dut__DOT__best_priority 
                    = (7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x37U] 
                             >> 0xdU));
                hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                    = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x36U] 
                                >> 5U));
                vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit 
                    = hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit;
            } else if (((IData)(hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit) 
                        & (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit))) {
                if (((7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x37U] 
                            >> 0xdU)) > (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_priority))) {
                    vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0xdU;
                    hbm_controller_tb_simple__DOT__dut__DOT__best_priority 
                        = (7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x37U] 
                                 >> 0xdU));
                    hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                        = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x36U] 
                                    >> 5U));
                } else if (((7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x37U] 
                                   >> 0xdU)) == (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_priority))) {
                    if (((0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x36U] 
                                   >> 5U)) < (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_age))) {
                        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0xdU;
                        hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                            = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x36U] 
                                        >> 5U));
                    }
                }
            } else if ((1U & ((~ (IData)(hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit)) 
                              & (~ (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit))))) {
                if (((7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x37U] 
                            >> 0xdU)) > (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_priority))) {
                    vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0xdU;
                    hbm_controller_tb_simple__DOT__dut__DOT__best_priority 
                        = (7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x37U] 
                                 >> 0xdU));
                    hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                        = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x36U] 
                                    >> 5U));
                } else if (((7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x37U] 
                                   >> 0xdU)) == (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_priority))) {
                    if (((0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x36U] 
                                   >> 5U)) < (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_age))) {
                        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0xdU;
                        hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                            = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x36U] 
                                        >> 5U));
                    }
                }
            }
        } else {
            vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0xdU;
            hbm_controller_tb_simple__DOT__dut__DOT__best_priority 
                = (7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x37U] 
                         >> 0xdU));
            hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x36U] 
                            >> 5U));
            vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit 
                = hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit;
            vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__grant_valid = 1U;
        }
    }
    hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit = 0U;
    if (((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x3eU] 
          >> 0xaU) & (0U == (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__state)))) {
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
            = (0xfffffffffULL & (((QData)((IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x3dU])) 
                                  << 0x1aU) | ((QData)((IData)(
                                                               vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x3cU])) 
                                               >> 6U)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch 
            = (0x1fU & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                                >> 0x1eU)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bg 
            = (7U & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                             >> 0x1aU)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_pch 
            = (1U & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                             >> 0x17U)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bank 
            = (0xfU & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                               >> 0x16U)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_row 
            = (0xffffU & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                                  >> 6U)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__Vfuncout 
            = (((((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__row_open 
                   >> ([&]() {
                                    vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__ch 
                                        = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                    vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__Vfuncout 
                                        = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__ch;
                                }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__Vfuncout))) 
                  & ((IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_pch) 
                     == (1U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_pch_reg 
                               >> ([&]() {
                                            vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__ch 
                                                = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                            vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__Vfuncout 
                                                = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__ch;
                                        }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__Vfuncout)))))) 
                 & ((IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bg) 
                    == ((0x5fU >= (0x7fU & ((IData)(3U) 
                                            * VL_EXTEND_II(32,5, 
                                                           ([&]() {
                                                    vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__ch 
                                                        = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                                    vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__Vfuncout 
                                                        = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__ch;
                                                }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__Vfuncout))))))
                         ? (7U & VL_SEL_IWII(96, vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_bg_reg, 
                                             (0x7fU 
                                              & ((IData)(3U) 
                                                 * 
                                                 VL_EXTEND_II(32,5, 
                                                              ([&]() {
                                                        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__ch 
                                                            = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                                        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__Vfuncout 
                                                            = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__ch;
                                                    }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__Vfuncout))))), 3U))
                         : 0U))) & ((IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bank) 
                                    == (0xfU & VL_SEL_IWII(128, vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_bank_reg, 
                                                           (0x7fU 
                                                            & VL_SHIFTL_III(7,32,32, 
                                                                            VL_EXTEND_II(32,5, 
                                                                                ([&]() {
                                                vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__ch 
                                                    = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                                vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__Vfuncout 
                                                    = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__ch;
                                            }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__Vfuncout))), 2U)), 4U)))) 
               & ((IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_row) 
                  == (0xffffU & VL_SEL_IWII(512, vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_row_reg, 
                                            (0x1ffU 
                                             & VL_SHIFTL_III(9,32,32, 
                                                             VL_EXTEND_II(32,5, 
                                                                          ([&]() {
                                            vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__ch 
                                                = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                            vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__Vfuncout 
                                                = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__ch;
                                        }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__Vfuncout))), 4U)), 0x10U))));
        hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit 
            = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__Vfuncout;
        if (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__grant_valid) {
            if (((IData)(hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit) 
                 & (~ (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit)))) {
                vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0xeU;
                hbm_controller_tb_simple__DOT__dut__DOT__best_priority 
                    = (7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x3bU] 
                             >> 0x12U));
                hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                    = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x3aU] 
                                >> 0xaU));
                vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit 
                    = hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit;
            } else if (((IData)(hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit) 
                        & (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit))) {
                if (((7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x3bU] 
                            >> 0x12U)) > (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_priority))) {
                    vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0xeU;
                    hbm_controller_tb_simple__DOT__dut__DOT__best_priority 
                        = (7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x3bU] 
                                 >> 0x12U));
                    hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                        = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x3aU] 
                                    >> 0xaU));
                } else if (((7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x3bU] 
                                   >> 0x12U)) == (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_priority))) {
                    if (((0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x3aU] 
                                   >> 0xaU)) < (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_age))) {
                        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0xeU;
                        hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                            = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x3aU] 
                                        >> 0xaU));
                    }
                }
            } else if ((1U & ((~ (IData)(hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit)) 
                              & (~ (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit))))) {
                if (((7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x3bU] 
                            >> 0x12U)) > (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_priority))) {
                    vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0xeU;
                    hbm_controller_tb_simple__DOT__dut__DOT__best_priority 
                        = (7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x3bU] 
                                 >> 0x12U));
                    hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                        = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x3aU] 
                                    >> 0xaU));
                } else if (((7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x3bU] 
                                   >> 0x12U)) == (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_priority))) {
                    if (((0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x3aU] 
                                   >> 0xaU)) < (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_age))) {
                        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0xeU;
                        hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                            = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x3aU] 
                                        >> 0xaU));
                    }
                }
            }
        } else {
            vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0xeU;
            hbm_controller_tb_simple__DOT__dut__DOT__best_priority 
                = (7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x3bU] 
                         >> 0x12U));
            hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x3aU] 
                            >> 0xaU));
            vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit 
                = hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit;
            vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__grant_valid = 1U;
        }
    }
    hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit = 0U;
    if (((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x42U] 
          >> 0xfU) & (0U == (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__state)))) {
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
            = (0xfffffffffULL & (((QData)((IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x41U])) 
                                  << 0x15U) | ((QData)((IData)(
                                                               vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x40U])) 
                                               >> 0xbU)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch 
            = (0x1fU & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                                >> 0x1eU)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bg 
            = (7U & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                             >> 0x1aU)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_pch 
            = (1U & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                             >> 0x17U)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bank 
            = (0xfU & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                               >> 0x16U)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_row 
            = (0xffffU & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                                  >> 6U)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__Vfuncout 
            = (((((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__row_open 
                   >> ([&]() {
                                    vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__ch 
                                        = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                    vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__Vfuncout 
                                        = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__ch;
                                }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__Vfuncout))) 
                  & ((IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_pch) 
                     == (1U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_pch_reg 
                               >> ([&]() {
                                            vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__ch 
                                                = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                            vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__Vfuncout 
                                                = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__ch;
                                        }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__Vfuncout)))))) 
                 & ((IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bg) 
                    == ((0x5fU >= (0x7fU & ((IData)(3U) 
                                            * VL_EXTEND_II(32,5, 
                                                           ([&]() {
                                                    vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__ch 
                                                        = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                                    vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__Vfuncout 
                                                        = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__ch;
                                                }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__Vfuncout))))))
                         ? (7U & VL_SEL_IWII(96, vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_bg_reg, 
                                             (0x7fU 
                                              & ((IData)(3U) 
                                                 * 
                                                 VL_EXTEND_II(32,5, 
                                                              ([&]() {
                                                        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__ch 
                                                            = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                                        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__Vfuncout 
                                                            = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__ch;
                                                    }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__Vfuncout))))), 3U))
                         : 0U))) & ((IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bank) 
                                    == (0xfU & VL_SEL_IWII(128, vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_bank_reg, 
                                                           (0x7fU 
                                                            & VL_SHIFTL_III(7,32,32, 
                                                                            VL_EXTEND_II(32,5, 
                                                                                ([&]() {
                                                vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__ch 
                                                    = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                                vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__Vfuncout 
                                                    = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__ch;
                                            }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__Vfuncout))), 2U)), 4U)))) 
               & ((IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_row) 
                  == (0xffffU & VL_SEL_IWII(512, vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_row_reg, 
                                            (0x1ffU 
                                             & VL_SHIFTL_III(9,32,32, 
                                                             VL_EXTEND_II(32,5, 
                                                                          ([&]() {
                                            vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__ch 
                                                = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                            vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__Vfuncout 
                                                = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__ch;
                                        }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__Vfuncout))), 4U)), 0x10U))));
        hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit 
            = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__Vfuncout;
        if (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__grant_valid) {
            if (((IData)(hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit) 
                 & (~ (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit)))) {
                vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0xfU;
                hbm_controller_tb_simple__DOT__dut__DOT__best_priority 
                    = (7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x3fU] 
                             >> 0x17U));
                hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                    = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x3eU] 
                                >> 0xfU));
                vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit 
                    = hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit;
            } else if (((IData)(hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit) 
                        & (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit))) {
                if (((7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x3fU] 
                            >> 0x17U)) > (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_priority))) {
                    vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0xfU;
                    hbm_controller_tb_simple__DOT__dut__DOT__best_priority 
                        = (7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x3fU] 
                                 >> 0x17U));
                    hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                        = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x3eU] 
                                    >> 0xfU));
                } else if (((7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x3fU] 
                                   >> 0x17U)) == (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_priority))) {
                    if (((0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x3eU] 
                                   >> 0xfU)) < (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_age))) {
                        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0xfU;
                        hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                            = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x3eU] 
                                        >> 0xfU));
                    }
                }
            } else if ((1U & ((~ (IData)(hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit)) 
                              & (~ (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit))))) {
                if (((7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x3fU] 
                            >> 0x17U)) > (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_priority))) {
                    vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0xfU;
                    hbm_controller_tb_simple__DOT__dut__DOT__best_priority 
                        = (7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x3fU] 
                                 >> 0x17U));
                    hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                        = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x3eU] 
                                    >> 0xfU));
                } else if (((7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x3fU] 
                                   >> 0x17U)) == (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_priority))) {
                    if (((0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x3eU] 
                                   >> 0xfU)) < (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_age))) {
                        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0xfU;
                        hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                            = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x3eU] 
                                        >> 0xfU));
                    }
                }
            }
        } else {
            vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0xfU;
            hbm_controller_tb_simple__DOT__dut__DOT__best_priority 
                = (7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x3fU] 
                         >> 0x17U));
            hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x3eU] 
                            >> 0xfU));
            vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit 
                = hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit;
            vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__grant_valid = 1U;
        }
    }
    hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit = 0U;
    if (((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x46U] 
          >> 0x14U) & (0U == (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__state)))) {
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
            = (0xfffffffffULL & (((QData)((IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x45U])) 
                                  << 0x10U) | ((QData)((IData)(
                                                               vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x44U])) 
                                               >> 0x10U)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch 
            = (0x1fU & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                                >> 0x1eU)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bg 
            = (7U & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                             >> 0x1aU)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_pch 
            = (1U & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                             >> 0x17U)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bank 
            = (0xfU & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                               >> 0x16U)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_row 
            = (0xffffU & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                                  >> 6U)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__Vfuncout 
            = (((((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__row_open 
                   >> ([&]() {
                                    vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__ch 
                                        = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                    vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__Vfuncout 
                                        = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__ch;
                                }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__Vfuncout))) 
                  & ((IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_pch) 
                     == (1U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_pch_reg 
                               >> ([&]() {
                                            vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__ch 
                                                = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                            vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__Vfuncout 
                                                = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__ch;
                                        }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__Vfuncout)))))) 
                 & ((IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bg) 
                    == ((0x5fU >= (0x7fU & ((IData)(3U) 
                                            * VL_EXTEND_II(32,5, 
                                                           ([&]() {
                                                    vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__ch 
                                                        = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                                    vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__Vfuncout 
                                                        = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__ch;
                                                }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__Vfuncout))))))
                         ? (7U & VL_SEL_IWII(96, vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_bg_reg, 
                                             (0x7fU 
                                              & ((IData)(3U) 
                                                 * 
                                                 VL_EXTEND_II(32,5, 
                                                              ([&]() {
                                                        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__ch 
                                                            = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                                        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__Vfuncout 
                                                            = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__ch;
                                                    }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__Vfuncout))))), 3U))
                         : 0U))) & ((IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bank) 
                                    == (0xfU & VL_SEL_IWII(128, vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_bank_reg, 
                                                           (0x7fU 
                                                            & VL_SHIFTL_III(7,32,32, 
                                                                            VL_EXTEND_II(32,5, 
                                                                                ([&]() {
                                                vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__ch 
                                                    = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                                vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__Vfuncout 
                                                    = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__ch;
                                            }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__Vfuncout))), 2U)), 4U)))) 
               & ((IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_row) 
                  == (0xffffU & VL_SEL_IWII(512, vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_row_reg, 
                                            (0x1ffU 
                                             & VL_SHIFTL_III(9,32,32, 
                                                             VL_EXTEND_II(32,5, 
                                                                          ([&]() {
                                            vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__ch 
                                                = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                            vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__Vfuncout 
                                                = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__ch;
                                        }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__Vfuncout))), 4U)), 0x10U))));
        hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit 
            = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__Vfuncout;
        if (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__grant_valid) {
            if (((IData)(hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit) 
                 & (~ (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit)))) {
                vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0x10U;
                hbm_controller_tb_simple__DOT__dut__DOT__best_priority 
                    = (7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x43U] 
                             >> 0x1cU));
                hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                    = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x42U] 
                                >> 0x14U));
                vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit 
                    = hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit;
            } else if (((IData)(hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit) 
                        & (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit))) {
                if (((7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x43U] 
                            >> 0x1cU)) > (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_priority))) {
                    vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0x10U;
                    hbm_controller_tb_simple__DOT__dut__DOT__best_priority 
                        = (7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x43U] 
                                 >> 0x1cU));
                    hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                        = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x42U] 
                                    >> 0x14U));
                } else if (((7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x43U] 
                                   >> 0x1cU)) == (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_priority))) {
                    if (((0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x42U] 
                                   >> 0x14U)) < (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_age))) {
                        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0x10U;
                        hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                            = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x42U] 
                                        >> 0x14U));
                    }
                }
            } else if ((1U & ((~ (IData)(hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit)) 
                              & (~ (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit))))) {
                if (((7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x43U] 
                            >> 0x1cU)) > (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_priority))) {
                    vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0x10U;
                    hbm_controller_tb_simple__DOT__dut__DOT__best_priority 
                        = (7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x43U] 
                                 >> 0x1cU));
                    hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                        = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x42U] 
                                    >> 0x14U));
                } else if (((7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x43U] 
                                   >> 0x1cU)) == (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_priority))) {
                    if (((0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x42U] 
                                   >> 0x14U)) < (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_age))) {
                        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0x10U;
                        hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                            = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x42U] 
                                        >> 0x14U));
                    }
                }
            }
        } else {
            vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0x10U;
            hbm_controller_tb_simple__DOT__dut__DOT__best_priority 
                = (7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x43U] 
                         >> 0x1cU));
            hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x42U] 
                            >> 0x14U));
            vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit 
                = hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit;
            vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__grant_valid = 1U;
        }
    }
    hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit = 0U;
    if (((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x4aU] 
          >> 0x19U) & (0U == (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__state)))) {
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
            = (0xfffffffffULL & (((QData)((IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x49U])) 
                                  << 0xbU) | ((QData)((IData)(
                                                              vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x48U])) 
                                              >> 0x15U)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch 
            = (0x1fU & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                                >> 0x1eU)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bg 
            = (7U & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                             >> 0x1aU)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_pch 
            = (1U & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                             >> 0x17U)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bank 
            = (0xfU & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                               >> 0x16U)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_row 
            = (0xffffU & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                                  >> 6U)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__Vfuncout 
            = (((((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__row_open 
                   >> ([&]() {
                                    vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__ch 
                                        = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                    vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__Vfuncout 
                                        = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__ch;
                                }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__Vfuncout))) 
                  & ((IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_pch) 
                     == (1U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_pch_reg 
                               >> ([&]() {
                                            vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__ch 
                                                = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                            vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__Vfuncout 
                                                = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__ch;
                                        }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__Vfuncout)))))) 
                 & ((IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bg) 
                    == ((0x5fU >= (0x7fU & ((IData)(3U) 
                                            * VL_EXTEND_II(32,5, 
                                                           ([&]() {
                                                    vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__ch 
                                                        = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                                    vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__Vfuncout 
                                                        = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__ch;
                                                }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__Vfuncout))))))
                         ? (7U & VL_SEL_IWII(96, vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_bg_reg, 
                                             (0x7fU 
                                              & ((IData)(3U) 
                                                 * 
                                                 VL_EXTEND_II(32,5, 
                                                              ([&]() {
                                                        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__ch 
                                                            = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                                        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__Vfuncout 
                                                            = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__ch;
                                                    }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__Vfuncout))))), 3U))
                         : 0U))) & ((IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bank) 
                                    == (0xfU & VL_SEL_IWII(128, vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_bank_reg, 
                                                           (0x7fU 
                                                            & VL_SHIFTL_III(7,32,32, 
                                                                            VL_EXTEND_II(32,5, 
                                                                                ([&]() {
                                                vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__ch 
                                                    = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                                vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__Vfuncout 
                                                    = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__ch;
                                            }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__Vfuncout))), 2U)), 4U)))) 
               & ((IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_row) 
                  == (0xffffU & VL_SEL_IWII(512, vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_row_reg, 
                                            (0x1ffU 
                                             & VL_SHIFTL_III(9,32,32, 
                                                             VL_EXTEND_II(32,5, 
                                                                          ([&]() {
                                            vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__ch 
                                                = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                            vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__Vfuncout 
                                                = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__ch;
                                        }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__Vfuncout))), 4U)), 0x10U))));
        hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit 
            = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__Vfuncout;
        if (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__grant_valid) {
            if (((IData)(hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit) 
                 & (~ (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit)))) {
                vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0x11U;
                hbm_controller_tb_simple__DOT__dut__DOT__best_priority 
                    = (7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x48U] 
                             >> 1U));
                hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                    = (0xffU & ((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x47U] 
                                 << 7U) | (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x46U] 
                                           >> 0x19U)));
                vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit 
                    = hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit;
            } else if (((IData)(hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit) 
                        & (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit))) {
                if (((7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x48U] 
                            >> 1U)) > (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_priority))) {
                    vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0x11U;
                    hbm_controller_tb_simple__DOT__dut__DOT__best_priority 
                        = (7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x48U] 
                                 >> 1U));
                    hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                        = (0xffU & ((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x47U] 
                                     << 7U) | (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x46U] 
                                               >> 0x19U)));
                } else if (((7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x48U] 
                                   >> 1U)) == (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_priority))) {
                    if (((0xffU & ((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x47U] 
                                    << 7U) | (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x46U] 
                                              >> 0x19U))) 
                         < (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_age))) {
                        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0x11U;
                        hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                            = (0xffU & ((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x47U] 
                                         << 7U) | (
                                                   vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x46U] 
                                                   >> 0x19U)));
                    }
                }
            } else if ((1U & ((~ (IData)(hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit)) 
                              & (~ (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit))))) {
                if (((7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x48U] 
                            >> 1U)) > (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_priority))) {
                    vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0x11U;
                    hbm_controller_tb_simple__DOT__dut__DOT__best_priority 
                        = (7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x48U] 
                                 >> 1U));
                    hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                        = (0xffU & ((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x47U] 
                                     << 7U) | (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x46U] 
                                               >> 0x19U)));
                } else if (((7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x48U] 
                                   >> 1U)) == (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_priority))) {
                    if (((0xffU & ((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x47U] 
                                    << 7U) | (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x46U] 
                                              >> 0x19U))) 
                         < (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_age))) {
                        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0x11U;
                        hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                            = (0xffU & ((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x47U] 
                                         << 7U) | (
                                                   vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x46U] 
                                                   >> 0x19U)));
                    }
                }
            }
        } else {
            vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0x11U;
            hbm_controller_tb_simple__DOT__dut__DOT__best_priority 
                = (7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x48U] 
                         >> 1U));
            hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                = (0xffU & ((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x47U] 
                             << 7U) | (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x46U] 
                                       >> 0x19U)));
            vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit 
                = hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit;
            vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__grant_valid = 1U;
        }
    }
    hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit = 0U;
    if (((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x4eU] 
          >> 0x1eU) & (0U == (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__state)))) {
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
            = (0xfffffffffULL & (((QData)((IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x4dU])) 
                                  << 6U) | ((QData)((IData)(
                                                            vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x4cU])) 
                                            >> 0x1aU)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch 
            = (0x1fU & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                                >> 0x1eU)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bg 
            = (7U & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                             >> 0x1aU)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_pch 
            = (1U & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                             >> 0x17U)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bank 
            = (0xfU & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                               >> 0x16U)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_row 
            = (0xffffU & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                                  >> 6U)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__Vfuncout 
            = (((((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__row_open 
                   >> ([&]() {
                                    vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__ch 
                                        = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                    vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__Vfuncout 
                                        = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__ch;
                                }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__Vfuncout))) 
                  & ((IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_pch) 
                     == (1U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_pch_reg 
                               >> ([&]() {
                                            vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__ch 
                                                = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                            vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__Vfuncout 
                                                = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__ch;
                                        }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__Vfuncout)))))) 
                 & ((IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bg) 
                    == ((0x5fU >= (0x7fU & ((IData)(3U) 
                                            * VL_EXTEND_II(32,5, 
                                                           ([&]() {
                                                    vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__ch 
                                                        = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                                    vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__Vfuncout 
                                                        = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__ch;
                                                }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__Vfuncout))))))
                         ? (7U & VL_SEL_IWII(96, vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_bg_reg, 
                                             (0x7fU 
                                              & ((IData)(3U) 
                                                 * 
                                                 VL_EXTEND_II(32,5, 
                                                              ([&]() {
                                                        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__ch 
                                                            = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                                        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__Vfuncout 
                                                            = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__ch;
                                                    }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__Vfuncout))))), 3U))
                         : 0U))) & ((IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bank) 
                                    == (0xfU & VL_SEL_IWII(128, vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_bank_reg, 
                                                           (0x7fU 
                                                            & VL_SHIFTL_III(7,32,32, 
                                                                            VL_EXTEND_II(32,5, 
                                                                                ([&]() {
                                                vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__ch 
                                                    = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                                vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__Vfuncout 
                                                    = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__ch;
                                            }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__Vfuncout))), 2U)), 4U)))) 
               & ((IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_row) 
                  == (0xffffU & VL_SEL_IWII(512, vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_row_reg, 
                                            (0x1ffU 
                                             & VL_SHIFTL_III(9,32,32, 
                                                             VL_EXTEND_II(32,5, 
                                                                          ([&]() {
                                            vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__ch 
                                                = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                            vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__Vfuncout 
                                                = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__ch;
                                        }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__Vfuncout))), 4U)), 0x10U))));
        hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit 
            = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__Vfuncout;
        if (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__grant_valid) {
            if (((IData)(hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit) 
                 & (~ (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit)))) {
                vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0x12U;
                hbm_controller_tb_simple__DOT__dut__DOT__best_priority 
                    = (7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x4cU] 
                             >> 6U));
                hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                    = (0xffU & ((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x4bU] 
                                 << 2U) | (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x4aU] 
                                           >> 0x1eU)));
                vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit 
                    = hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit;
            } else if (((IData)(hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit) 
                        & (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit))) {
                if (((7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x4cU] 
                            >> 6U)) > (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_priority))) {
                    vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0x12U;
                    hbm_controller_tb_simple__DOT__dut__DOT__best_priority 
                        = (7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x4cU] 
                                 >> 6U));
                    hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                        = (0xffU & ((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x4bU] 
                                     << 2U) | (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x4aU] 
                                               >> 0x1eU)));
                } else if (((7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x4cU] 
                                   >> 6U)) == (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_priority))) {
                    if (((0xffU & ((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x4bU] 
                                    << 2U) | (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x4aU] 
                                              >> 0x1eU))) 
                         < (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_age))) {
                        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0x12U;
                        hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                            = (0xffU & ((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x4bU] 
                                         << 2U) | (
                                                   vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x4aU] 
                                                   >> 0x1eU)));
                    }
                }
            } else if ((1U & ((~ (IData)(hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit)) 
                              & (~ (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit))))) {
                if (((7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x4cU] 
                            >> 6U)) > (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_priority))) {
                    vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0x12U;
                    hbm_controller_tb_simple__DOT__dut__DOT__best_priority 
                        = (7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x4cU] 
                                 >> 6U));
                    hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                        = (0xffU & ((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x4bU] 
                                     << 2U) | (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x4aU] 
                                               >> 0x1eU)));
                } else if (((7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x4cU] 
                                   >> 6U)) == (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_priority))) {
                    if (((0xffU & ((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x4bU] 
                                    << 2U) | (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x4aU] 
                                              >> 0x1eU))) 
                         < (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_age))) {
                        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0x12U;
                        hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                            = (0xffU & ((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x4bU] 
                                         << 2U) | (
                                                   vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x4aU] 
                                                   >> 0x1eU)));
                    }
                }
            }
        } else {
            vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0x12U;
            hbm_controller_tb_simple__DOT__dut__DOT__best_priority 
                = (7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x4cU] 
                         >> 6U));
            hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                = (0xffU & ((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x4bU] 
                             << 2U) | (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x4aU] 
                                       >> 0x1eU)));
            vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit 
                = hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit;
            vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__grant_valid = 1U;
        }
    }
    hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit = 0U;
    if (((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x53U] 
          >> 3U) & (0U == (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__state)))) {
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
            = (0xfffffffffULL & (((QData)((IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x52U])) 
                                  << 0x21U) | (((QData)((IData)(
                                                                vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x51U])) 
                                                << 1U) 
                                               | ((QData)((IData)(
                                                                  vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x50U])) 
                                                  >> 0x1fU))));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch 
            = (0x1fU & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                                >> 0x1eU)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bg 
            = (7U & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                             >> 0x1aU)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_pch 
            = (1U & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                             >> 0x17U)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bank 
            = (0xfU & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                               >> 0x16U)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_row 
            = (0xffffU & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                                  >> 6U)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__Vfuncout 
            = (((((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__row_open 
                   >> ([&]() {
                                    vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__ch 
                                        = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                    vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__Vfuncout 
                                        = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__ch;
                                }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__Vfuncout))) 
                  & ((IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_pch) 
                     == (1U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_pch_reg 
                               >> ([&]() {
                                            vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__ch 
                                                = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                            vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__Vfuncout 
                                                = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__ch;
                                        }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__Vfuncout)))))) 
                 & ((IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bg) 
                    == ((0x5fU >= (0x7fU & ((IData)(3U) 
                                            * VL_EXTEND_II(32,5, 
                                                           ([&]() {
                                                    vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__ch 
                                                        = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                                    vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__Vfuncout 
                                                        = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__ch;
                                                }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__Vfuncout))))))
                         ? (7U & VL_SEL_IWII(96, vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_bg_reg, 
                                             (0x7fU 
                                              & ((IData)(3U) 
                                                 * 
                                                 VL_EXTEND_II(32,5, 
                                                              ([&]() {
                                                        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__ch 
                                                            = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                                        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__Vfuncout 
                                                            = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__ch;
                                                    }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__Vfuncout))))), 3U))
                         : 0U))) & ((IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bank) 
                                    == (0xfU & VL_SEL_IWII(128, vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_bank_reg, 
                                                           (0x7fU 
                                                            & VL_SHIFTL_III(7,32,32, 
                                                                            VL_EXTEND_II(32,5, 
                                                                                ([&]() {
                                                vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__ch 
                                                    = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                                vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__Vfuncout 
                                                    = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__ch;
                                            }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__Vfuncout))), 2U)), 4U)))) 
               & ((IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_row) 
                  == (0xffffU & VL_SEL_IWII(512, vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_row_reg, 
                                            (0x1ffU 
                                             & VL_SHIFTL_III(9,32,32, 
                                                             VL_EXTEND_II(32,5, 
                                                                          ([&]() {
                                            vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__ch 
                                                = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                            vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__Vfuncout 
                                                = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__ch;
                                        }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__Vfuncout))), 4U)), 0x10U))));
        hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit 
            = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__Vfuncout;
        if (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__grant_valid) {
            if (((IData)(hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit) 
                 & (~ (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit)))) {
                vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0x13U;
                hbm_controller_tb_simple__DOT__dut__DOT__best_priority 
                    = (7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x50U] 
                             >> 0xbU));
                hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                    = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x4fU] 
                                >> 3U));
                vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit 
                    = hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit;
            } else if (((IData)(hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit) 
                        & (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit))) {
                if (((7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x50U] 
                            >> 0xbU)) > (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_priority))) {
                    vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0x13U;
                    hbm_controller_tb_simple__DOT__dut__DOT__best_priority 
                        = (7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x50U] 
                                 >> 0xbU));
                    hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                        = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x4fU] 
                                    >> 3U));
                } else if (((7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x50U] 
                                   >> 0xbU)) == (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_priority))) {
                    if (((0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x4fU] 
                                   >> 3U)) < (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_age))) {
                        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0x13U;
                        hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                            = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x4fU] 
                                        >> 3U));
                    }
                }
            } else if ((1U & ((~ (IData)(hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit)) 
                              & (~ (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit))))) {
                if (((7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x50U] 
                            >> 0xbU)) > (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_priority))) {
                    vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0x13U;
                    hbm_controller_tb_simple__DOT__dut__DOT__best_priority 
                        = (7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x50U] 
                                 >> 0xbU));
                    hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                        = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x4fU] 
                                    >> 3U));
                } else if (((7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x50U] 
                                   >> 0xbU)) == (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_priority))) {
                    if (((0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x4fU] 
                                   >> 3U)) < (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_age))) {
                        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0x13U;
                        hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                            = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x4fU] 
                                        >> 3U));
                    }
                }
            }
        } else {
            vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0x13U;
            hbm_controller_tb_simple__DOT__dut__DOT__best_priority 
                = (7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x50U] 
                         >> 0xbU));
            hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x4fU] 
                            >> 3U));
            vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit 
                = hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit;
            vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__grant_valid = 1U;
        }
    }
    hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit = 0U;
    if (((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x57U] 
          >> 8U) & (0U == (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__state)))) {
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
            = (0xfffffffffULL & (((QData)((IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x56U])) 
                                  << 0x1cU) | ((QData)((IData)(
                                                               vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x55U])) 
                                               >> 4U)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch 
            = (0x1fU & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                                >> 0x1eU)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bg 
            = (7U & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                             >> 0x1aU)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_pch 
            = (1U & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                             >> 0x17U)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bank 
            = (0xfU & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                               >> 0x16U)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_row 
            = (0xffffU & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                                  >> 6U)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__Vfuncout 
            = (((((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__row_open 
                   >> ([&]() {
                                    vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__ch 
                                        = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                    vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__Vfuncout 
                                        = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__ch;
                                }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__Vfuncout))) 
                  & ((IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_pch) 
                     == (1U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_pch_reg 
                               >> ([&]() {
                                            vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__ch 
                                                = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                            vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__Vfuncout 
                                                = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__ch;
                                        }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__Vfuncout)))))) 
                 & ((IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bg) 
                    == ((0x5fU >= (0x7fU & ((IData)(3U) 
                                            * VL_EXTEND_II(32,5, 
                                                           ([&]() {
                                                    vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__ch 
                                                        = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                                    vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__Vfuncout 
                                                        = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__ch;
                                                }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__Vfuncout))))))
                         ? (7U & VL_SEL_IWII(96, vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_bg_reg, 
                                             (0x7fU 
                                              & ((IData)(3U) 
                                                 * 
                                                 VL_EXTEND_II(32,5, 
                                                              ([&]() {
                                                        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__ch 
                                                            = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                                        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__Vfuncout 
                                                            = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__ch;
                                                    }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__Vfuncout))))), 3U))
                         : 0U))) & ((IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bank) 
                                    == (0xfU & VL_SEL_IWII(128, vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_bank_reg, 
                                                           (0x7fU 
                                                            & VL_SHIFTL_III(7,32,32, 
                                                                            VL_EXTEND_II(32,5, 
                                                                                ([&]() {
                                                vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__ch 
                                                    = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                                vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__Vfuncout 
                                                    = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__ch;
                                            }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__Vfuncout))), 2U)), 4U)))) 
               & ((IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_row) 
                  == (0xffffU & VL_SEL_IWII(512, vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_row_reg, 
                                            (0x1ffU 
                                             & VL_SHIFTL_III(9,32,32, 
                                                             VL_EXTEND_II(32,5, 
                                                                          ([&]() {
                                            vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__ch 
                                                = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                            vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__Vfuncout 
                                                = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__ch;
                                        }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__Vfuncout))), 4U)), 0x10U))));
        hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit 
            = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__Vfuncout;
        if (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__grant_valid) {
            if (((IData)(hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit) 
                 & (~ (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit)))) {
                vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0x14U;
                hbm_controller_tb_simple__DOT__dut__DOT__best_priority 
                    = (7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x54U] 
                             >> 0x10U));
                hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                    = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x53U] 
                                >> 8U));
                vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit 
                    = hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit;
            } else if (((IData)(hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit) 
                        & (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit))) {
                if (((7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x54U] 
                            >> 0x10U)) > (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_priority))) {
                    vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0x14U;
                    hbm_controller_tb_simple__DOT__dut__DOT__best_priority 
                        = (7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x54U] 
                                 >> 0x10U));
                    hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                        = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x53U] 
                                    >> 8U));
                } else if (((7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x54U] 
                                   >> 0x10U)) == (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_priority))) {
                    if (((0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x53U] 
                                   >> 8U)) < (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_age))) {
                        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0x14U;
                        hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                            = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x53U] 
                                        >> 8U));
                    }
                }
            } else if ((1U & ((~ (IData)(hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit)) 
                              & (~ (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit))))) {
                if (((7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x54U] 
                            >> 0x10U)) > (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_priority))) {
                    vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0x14U;
                    hbm_controller_tb_simple__DOT__dut__DOT__best_priority 
                        = (7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x54U] 
                                 >> 0x10U));
                    hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                        = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x53U] 
                                    >> 8U));
                } else if (((7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x54U] 
                                   >> 0x10U)) == (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_priority))) {
                    if (((0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x53U] 
                                   >> 8U)) < (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_age))) {
                        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0x14U;
                        hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                            = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x53U] 
                                        >> 8U));
                    }
                }
            }
        } else {
            vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0x14U;
            hbm_controller_tb_simple__DOT__dut__DOT__best_priority 
                = (7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x54U] 
                         >> 0x10U));
            hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x53U] 
                            >> 8U));
            vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit 
                = hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit;
            vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__grant_valid = 1U;
        }
    }
    hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit = 0U;
    if (((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x5bU] 
          >> 0xdU) & (0U == (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__state)))) {
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
            = (0xfffffffffULL & (((QData)((IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x5aU])) 
                                  << 0x17U) | ((QData)((IData)(
                                                               vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x59U])) 
                                               >> 9U)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch 
            = (0x1fU & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                                >> 0x1eU)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bg 
            = (7U & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                             >> 0x1aU)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_pch 
            = (1U & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                             >> 0x17U)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bank 
            = (0xfU & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                               >> 0x16U)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_row 
            = (0xffffU & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                                  >> 6U)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__Vfuncout 
            = (((((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__row_open 
                   >> ([&]() {
                                    vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__ch 
                                        = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                    vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__Vfuncout 
                                        = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__ch;
                                }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__Vfuncout))) 
                  & ((IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_pch) 
                     == (1U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_pch_reg 
                               >> ([&]() {
                                            vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__ch 
                                                = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                            vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__Vfuncout 
                                                = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__ch;
                                        }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__Vfuncout)))))) 
                 & ((IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bg) 
                    == ((0x5fU >= (0x7fU & ((IData)(3U) 
                                            * VL_EXTEND_II(32,5, 
                                                           ([&]() {
                                                    vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__ch 
                                                        = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                                    vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__Vfuncout 
                                                        = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__ch;
                                                }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__Vfuncout))))))
                         ? (7U & VL_SEL_IWII(96, vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_bg_reg, 
                                             (0x7fU 
                                              & ((IData)(3U) 
                                                 * 
                                                 VL_EXTEND_II(32,5, 
                                                              ([&]() {
                                                        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__ch 
                                                            = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                                        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__Vfuncout 
                                                            = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__ch;
                                                    }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__Vfuncout))))), 3U))
                         : 0U))) & ((IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bank) 
                                    == (0xfU & VL_SEL_IWII(128, vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_bank_reg, 
                                                           (0x7fU 
                                                            & VL_SHIFTL_III(7,32,32, 
                                                                            VL_EXTEND_II(32,5, 
                                                                                ([&]() {
                                                vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__ch 
                                                    = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                                vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__Vfuncout 
                                                    = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__ch;
                                            }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__Vfuncout))), 2U)), 4U)))) 
               & ((IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_row) 
                  == (0xffffU & VL_SEL_IWII(512, vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_row_reg, 
                                            (0x1ffU 
                                             & VL_SHIFTL_III(9,32,32, 
                                                             VL_EXTEND_II(32,5, 
                                                                          ([&]() {
                                            vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__ch 
                                                = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                            vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__Vfuncout 
                                                = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__ch;
                                        }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__Vfuncout))), 4U)), 0x10U))));
        hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit 
            = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__Vfuncout;
        if (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__grant_valid) {
            if (((IData)(hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit) 
                 & (~ (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit)))) {
                vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0x15U;
                hbm_controller_tb_simple__DOT__dut__DOT__best_priority 
                    = (7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x58U] 
                             >> 0x15U));
                hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                    = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x57U] 
                                >> 0xdU));
                vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit 
                    = hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit;
            } else if (((IData)(hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit) 
                        & (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit))) {
                if (((7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x58U] 
                            >> 0x15U)) > (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_priority))) {
                    vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0x15U;
                    hbm_controller_tb_simple__DOT__dut__DOT__best_priority 
                        = (7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x58U] 
                                 >> 0x15U));
                    hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                        = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x57U] 
                                    >> 0xdU));
                } else if (((7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x58U] 
                                   >> 0x15U)) == (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_priority))) {
                    if (((0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x57U] 
                                   >> 0xdU)) < (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_age))) {
                        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0x15U;
                        hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                            = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x57U] 
                                        >> 0xdU));
                    }
                }
            } else if ((1U & ((~ (IData)(hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit)) 
                              & (~ (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit))))) {
                if (((7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x58U] 
                            >> 0x15U)) > (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_priority))) {
                    vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0x15U;
                    hbm_controller_tb_simple__DOT__dut__DOT__best_priority 
                        = (7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x58U] 
                                 >> 0x15U));
                    hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                        = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x57U] 
                                    >> 0xdU));
                } else if (((7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x58U] 
                                   >> 0x15U)) == (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_priority))) {
                    if (((0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x57U] 
                                   >> 0xdU)) < (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_age))) {
                        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0x15U;
                        hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                            = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x57U] 
                                        >> 0xdU));
                    }
                }
            }
        } else {
            vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0x15U;
            hbm_controller_tb_simple__DOT__dut__DOT__best_priority 
                = (7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x58U] 
                         >> 0x15U));
            hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x57U] 
                            >> 0xdU));
            vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit 
                = hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit;
            vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__grant_valid = 1U;
        }
    }
    hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit = 0U;
    if (((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x5fU] 
          >> 0x12U) & (0U == (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__state)))) {
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
            = (0xfffffffffULL & (((QData)((IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x5eU])) 
                                  << 0x12U) | ((QData)((IData)(
                                                               vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x5dU])) 
                                               >> 0xeU)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch 
            = (0x1fU & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                                >> 0x1eU)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bg 
            = (7U & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                             >> 0x1aU)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_pch 
            = (1U & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                             >> 0x17U)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bank 
            = (0xfU & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                               >> 0x16U)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_row 
            = (0xffffU & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                                  >> 6U)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__Vfuncout 
            = (((((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__row_open 
                   >> ([&]() {
                                    vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__ch 
                                        = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                    vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__Vfuncout 
                                        = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__ch;
                                }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__Vfuncout))) 
                  & ((IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_pch) 
                     == (1U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_pch_reg 
                               >> ([&]() {
                                            vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__ch 
                                                = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                            vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__Vfuncout 
                                                = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__ch;
                                        }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__Vfuncout)))))) 
                 & ((IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bg) 
                    == ((0x5fU >= (0x7fU & ((IData)(3U) 
                                            * VL_EXTEND_II(32,5, 
                                                           ([&]() {
                                                    vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__ch 
                                                        = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                                    vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__Vfuncout 
                                                        = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__ch;
                                                }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__Vfuncout))))))
                         ? (7U & VL_SEL_IWII(96, vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_bg_reg, 
                                             (0x7fU 
                                              & ((IData)(3U) 
                                                 * 
                                                 VL_EXTEND_II(32,5, 
                                                              ([&]() {
                                                        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__ch 
                                                            = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                                        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__Vfuncout 
                                                            = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__ch;
                                                    }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__Vfuncout))))), 3U))
                         : 0U))) & ((IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bank) 
                                    == (0xfU & VL_SEL_IWII(128, vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_bank_reg, 
                                                           (0x7fU 
                                                            & VL_SHIFTL_III(7,32,32, 
                                                                            VL_EXTEND_II(32,5, 
                                                                                ([&]() {
                                                vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__ch 
                                                    = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                                vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__Vfuncout 
                                                    = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__ch;
                                            }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__Vfuncout))), 2U)), 4U)))) 
               & ((IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_row) 
                  == (0xffffU & VL_SEL_IWII(512, vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_row_reg, 
                                            (0x1ffU 
                                             & VL_SHIFTL_III(9,32,32, 
                                                             VL_EXTEND_II(32,5, 
                                                                          ([&]() {
                                            vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__ch 
                                                = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                            vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__Vfuncout 
                                                = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__ch;
                                        }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__Vfuncout))), 4U)), 0x10U))));
        hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit 
            = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__Vfuncout;
        if (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__grant_valid) {
            if (((IData)(hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit) 
                 & (~ (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit)))) {
                vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0x16U;
                hbm_controller_tb_simple__DOT__dut__DOT__best_priority 
                    = (7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x5cU] 
                             >> 0x1aU));
                hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                    = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x5bU] 
                                >> 0x12U));
                vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit 
                    = hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit;
            } else if (((IData)(hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit) 
                        & (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit))) {
                if (((7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x5cU] 
                            >> 0x1aU)) > (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_priority))) {
                    vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0x16U;
                    hbm_controller_tb_simple__DOT__dut__DOT__best_priority 
                        = (7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x5cU] 
                                 >> 0x1aU));
                    hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                        = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x5bU] 
                                    >> 0x12U));
                } else if (((7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x5cU] 
                                   >> 0x1aU)) == (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_priority))) {
                    if (((0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x5bU] 
                                   >> 0x12U)) < (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_age))) {
                        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0x16U;
                        hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                            = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x5bU] 
                                        >> 0x12U));
                    }
                }
            } else if ((1U & ((~ (IData)(hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit)) 
                              & (~ (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit))))) {
                if (((7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x5cU] 
                            >> 0x1aU)) > (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_priority))) {
                    vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0x16U;
                    hbm_controller_tb_simple__DOT__dut__DOT__best_priority 
                        = (7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x5cU] 
                                 >> 0x1aU));
                    hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                        = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x5bU] 
                                    >> 0x12U));
                } else if (((7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x5cU] 
                                   >> 0x1aU)) == (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_priority))) {
                    if (((0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x5bU] 
                                   >> 0x12U)) < (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_age))) {
                        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0x16U;
                        hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                            = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x5bU] 
                                        >> 0x12U));
                    }
                }
            }
        } else {
            vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0x16U;
            hbm_controller_tb_simple__DOT__dut__DOT__best_priority 
                = (7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x5cU] 
                         >> 0x1aU));
            hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x5bU] 
                            >> 0x12U));
            vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit 
                = hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit;
            vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__grant_valid = 1U;
        }
    }
    hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit = 0U;
    if (((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x63U] 
          >> 0x17U) & (0U == (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__state)))) {
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
            = (0xfffffffffULL & (((QData)((IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x62U])) 
                                  << 0xdU) | ((QData)((IData)(
                                                              vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x61U])) 
                                              >> 0x13U)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch 
            = (0x1fU & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                                >> 0x1eU)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bg 
            = (7U & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                             >> 0x1aU)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_pch 
            = (1U & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                             >> 0x17U)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bank 
            = (0xfU & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                               >> 0x16U)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_row 
            = (0xffffU & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                                  >> 6U)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__Vfuncout 
            = (((((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__row_open 
                   >> ([&]() {
                                    vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__ch 
                                        = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                    vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__Vfuncout 
                                        = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__ch;
                                }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__Vfuncout))) 
                  & ((IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_pch) 
                     == (1U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_pch_reg 
                               >> ([&]() {
                                            vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__ch 
                                                = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                            vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__Vfuncout 
                                                = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__ch;
                                        }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__Vfuncout)))))) 
                 & ((IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bg) 
                    == ((0x5fU >= (0x7fU & ((IData)(3U) 
                                            * VL_EXTEND_II(32,5, 
                                                           ([&]() {
                                                    vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__ch 
                                                        = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                                    vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__Vfuncout 
                                                        = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__ch;
                                                }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__Vfuncout))))))
                         ? (7U & VL_SEL_IWII(96, vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_bg_reg, 
                                             (0x7fU 
                                              & ((IData)(3U) 
                                                 * 
                                                 VL_EXTEND_II(32,5, 
                                                              ([&]() {
                                                        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__ch 
                                                            = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                                        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__Vfuncout 
                                                            = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__ch;
                                                    }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__Vfuncout))))), 3U))
                         : 0U))) & ((IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bank) 
                                    == (0xfU & VL_SEL_IWII(128, vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_bank_reg, 
                                                           (0x7fU 
                                                            & VL_SHIFTL_III(7,32,32, 
                                                                            VL_EXTEND_II(32,5, 
                                                                                ([&]() {
                                                vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__ch 
                                                    = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                                vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__Vfuncout 
                                                    = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__ch;
                                            }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__Vfuncout))), 2U)), 4U)))) 
               & ((IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_row) 
                  == (0xffffU & VL_SEL_IWII(512, vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_row_reg, 
                                            (0x1ffU 
                                             & VL_SHIFTL_III(9,32,32, 
                                                             VL_EXTEND_II(32,5, 
                                                                          ([&]() {
                                            vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__ch 
                                                = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                            vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__Vfuncout 
                                                = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__ch;
                                        }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__Vfuncout))), 4U)), 0x10U))));
        hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit 
            = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__Vfuncout;
        if (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__grant_valid) {
            if (((IData)(hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit) 
                 & (~ (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit)))) {
                vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0x17U;
                hbm_controller_tb_simple__DOT__dut__DOT__best_priority 
                    = (7U & ((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x61U] 
                              << 1U) | (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x60U] 
                                        >> 0x1fU)));
                hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                    = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x5fU] 
                                >> 0x17U));
                vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit 
                    = hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit;
            } else if (((IData)(hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit) 
                        & (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit))) {
                if (((7U & ((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x61U] 
                             << 1U) | (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x60U] 
                                       >> 0x1fU))) 
                     > (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_priority))) {
                    vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0x17U;
                    hbm_controller_tb_simple__DOT__dut__DOT__best_priority 
                        = (7U & ((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x61U] 
                                  << 1U) | (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x60U] 
                                            >> 0x1fU)));
                    hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                        = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x5fU] 
                                    >> 0x17U));
                } else if (((7U & ((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x61U] 
                                    << 1U) | (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x60U] 
                                              >> 0x1fU))) 
                            == (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_priority))) {
                    if (((0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x5fU] 
                                   >> 0x17U)) < (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_age))) {
                        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0x17U;
                        hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                            = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x5fU] 
                                        >> 0x17U));
                    }
                }
            } else if ((1U & ((~ (IData)(hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit)) 
                              & (~ (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit))))) {
                if (((7U & ((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x61U] 
                             << 1U) | (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x60U] 
                                       >> 0x1fU))) 
                     > (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_priority))) {
                    vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0x17U;
                    hbm_controller_tb_simple__DOT__dut__DOT__best_priority 
                        = (7U & ((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x61U] 
                                  << 1U) | (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x60U] 
                                            >> 0x1fU)));
                    hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                        = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x5fU] 
                                    >> 0x17U));
                } else if (((7U & ((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x61U] 
                                    << 1U) | (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x60U] 
                                              >> 0x1fU))) 
                            == (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_priority))) {
                    if (((0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x5fU] 
                                   >> 0x17U)) < (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_age))) {
                        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0x17U;
                        hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                            = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x5fU] 
                                        >> 0x17U));
                    }
                }
            }
        } else {
            vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0x17U;
            hbm_controller_tb_simple__DOT__dut__DOT__best_priority 
                = (7U & ((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x61U] 
                          << 1U) | (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x60U] 
                                    >> 0x1fU)));
            hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x5fU] 
                            >> 0x17U));
            vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit 
                = hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit;
            vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__grant_valid = 1U;
        }
    }
    hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit = 0U;
    if (((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x67U] 
          >> 0x1cU) & (0U == (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__state)))) {
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
            = (0xfffffffffULL & (((QData)((IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x66U])) 
                                  << 8U) | ((QData)((IData)(
                                                            vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x65U])) 
                                            >> 0x18U)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch 
            = (0x1fU & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                                >> 0x1eU)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bg 
            = (7U & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                             >> 0x1aU)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_pch 
            = (1U & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                             >> 0x17U)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bank 
            = (0xfU & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                               >> 0x16U)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_row 
            = (0xffffU & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                                  >> 6U)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__Vfuncout 
            = (((((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__row_open 
                   >> ([&]() {
                                    vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__ch 
                                        = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                    vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__Vfuncout 
                                        = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__ch;
                                }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__Vfuncout))) 
                  & ((IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_pch) 
                     == (1U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_pch_reg 
                               >> ([&]() {
                                            vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__ch 
                                                = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                            vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__Vfuncout 
                                                = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__ch;
                                        }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__Vfuncout)))))) 
                 & ((IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bg) 
                    == ((0x5fU >= (0x7fU & ((IData)(3U) 
                                            * VL_EXTEND_II(32,5, 
                                                           ([&]() {
                                                    vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__ch 
                                                        = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                                    vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__Vfuncout 
                                                        = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__ch;
                                                }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__Vfuncout))))))
                         ? (7U & VL_SEL_IWII(96, vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_bg_reg, 
                                             (0x7fU 
                                              & ((IData)(3U) 
                                                 * 
                                                 VL_EXTEND_II(32,5, 
                                                              ([&]() {
                                                        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__ch 
                                                            = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                                        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__Vfuncout 
                                                            = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__ch;
                                                    }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__Vfuncout))))), 3U))
                         : 0U))) & ((IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bank) 
                                    == (0xfU & VL_SEL_IWII(128, vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_bank_reg, 
                                                           (0x7fU 
                                                            & VL_SHIFTL_III(7,32,32, 
                                                                            VL_EXTEND_II(32,5, 
                                                                                ([&]() {
                                                vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__ch 
                                                    = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                                vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__Vfuncout 
                                                    = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__ch;
                                            }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__Vfuncout))), 2U)), 4U)))) 
               & ((IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_row) 
                  == (0xffffU & VL_SEL_IWII(512, vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_row_reg, 
                                            (0x1ffU 
                                             & VL_SHIFTL_III(9,32,32, 
                                                             VL_EXTEND_II(32,5, 
                                                                          ([&]() {
                                            vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__ch 
                                                = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                            vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__Vfuncout 
                                                = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__ch;
                                        }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__Vfuncout))), 4U)), 0x10U))));
        hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit 
            = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__Vfuncout;
        if (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__grant_valid) {
            if (((IData)(hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit) 
                 & (~ (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit)))) {
                vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0x18U;
                hbm_controller_tb_simple__DOT__dut__DOT__best_priority 
                    = (7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x65U] 
                             >> 4U));
                hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                    = (0xffU & ((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x64U] 
                                 << 4U) | (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x63U] 
                                           >> 0x1cU)));
                vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit 
                    = hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit;
            } else if (((IData)(hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit) 
                        & (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit))) {
                if (((7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x65U] 
                            >> 4U)) > (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_priority))) {
                    vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0x18U;
                    hbm_controller_tb_simple__DOT__dut__DOT__best_priority 
                        = (7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x65U] 
                                 >> 4U));
                    hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                        = (0xffU & ((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x64U] 
                                     << 4U) | (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x63U] 
                                               >> 0x1cU)));
                } else if (((7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x65U] 
                                   >> 4U)) == (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_priority))) {
                    if (((0xffU & ((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x64U] 
                                    << 4U) | (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x63U] 
                                              >> 0x1cU))) 
                         < (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_age))) {
                        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0x18U;
                        hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                            = (0xffU & ((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x64U] 
                                         << 4U) | (
                                                   vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x63U] 
                                                   >> 0x1cU)));
                    }
                }
            } else if ((1U & ((~ (IData)(hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit)) 
                              & (~ (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit))))) {
                if (((7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x65U] 
                            >> 4U)) > (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_priority))) {
                    vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0x18U;
                    hbm_controller_tb_simple__DOT__dut__DOT__best_priority 
                        = (7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x65U] 
                                 >> 4U));
                    hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                        = (0xffU & ((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x64U] 
                                     << 4U) | (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x63U] 
                                               >> 0x1cU)));
                } else if (((7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x65U] 
                                   >> 4U)) == (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_priority))) {
                    if (((0xffU & ((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x64U] 
                                    << 4U) | (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x63U] 
                                              >> 0x1cU))) 
                         < (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_age))) {
                        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0x18U;
                        hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                            = (0xffU & ((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x64U] 
                                         << 4U) | (
                                                   vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x63U] 
                                                   >> 0x1cU)));
                    }
                }
            }
        } else {
            vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0x18U;
            hbm_controller_tb_simple__DOT__dut__DOT__best_priority 
                = (7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x65U] 
                         >> 4U));
            hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                = (0xffU & ((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x64U] 
                             << 4U) | (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x63U] 
                                       >> 0x1cU)));
            vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit 
                = hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit;
            vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__grant_valid = 1U;
        }
    }
    hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit = 0U;
    if (((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x6cU] 
          >> 1U) & (0U == (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__state)))) {
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
            = (0xfffffffffULL & (((QData)((IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x6bU])) 
                                  << 0x23U) | (((QData)((IData)(
                                                                vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x6aU])) 
                                                << 3U) 
                                               | ((QData)((IData)(
                                                                  vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x69U])) 
                                                  >> 0x1dU))));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch 
            = (0x1fU & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                                >> 0x1eU)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bg 
            = (7U & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                             >> 0x1aU)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_pch 
            = (1U & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                             >> 0x17U)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bank 
            = (0xfU & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                               >> 0x16U)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_row 
            = (0xffffU & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                                  >> 6U)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__Vfuncout 
            = (((((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__row_open 
                   >> ([&]() {
                                    vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__ch 
                                        = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                    vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__Vfuncout 
                                        = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__ch;
                                }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__Vfuncout))) 
                  & ((IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_pch) 
                     == (1U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_pch_reg 
                               >> ([&]() {
                                            vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__ch 
                                                = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                            vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__Vfuncout 
                                                = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__ch;
                                        }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__Vfuncout)))))) 
                 & ((IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bg) 
                    == ((0x5fU >= (0x7fU & ((IData)(3U) 
                                            * VL_EXTEND_II(32,5, 
                                                           ([&]() {
                                                    vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__ch 
                                                        = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                                    vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__Vfuncout 
                                                        = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__ch;
                                                }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__Vfuncout))))))
                         ? (7U & VL_SEL_IWII(96, vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_bg_reg, 
                                             (0x7fU 
                                              & ((IData)(3U) 
                                                 * 
                                                 VL_EXTEND_II(32,5, 
                                                              ([&]() {
                                                        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__ch 
                                                            = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                                        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__Vfuncout 
                                                            = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__ch;
                                                    }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__Vfuncout))))), 3U))
                         : 0U))) & ((IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bank) 
                                    == (0xfU & VL_SEL_IWII(128, vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_bank_reg, 
                                                           (0x7fU 
                                                            & VL_SHIFTL_III(7,32,32, 
                                                                            VL_EXTEND_II(32,5, 
                                                                                ([&]() {
                                                vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__ch 
                                                    = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                                vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__Vfuncout 
                                                    = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__ch;
                                            }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__Vfuncout))), 2U)), 4U)))) 
               & ((IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_row) 
                  == (0xffffU & VL_SEL_IWII(512, vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_row_reg, 
                                            (0x1ffU 
                                             & VL_SHIFTL_III(9,32,32, 
                                                             VL_EXTEND_II(32,5, 
                                                                          ([&]() {
                                            vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__ch 
                                                = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                            vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__Vfuncout 
                                                = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__ch;
                                        }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__Vfuncout))), 4U)), 0x10U))));
        hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit 
            = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__Vfuncout;
        if (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__grant_valid) {
            if (((IData)(hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit) 
                 & (~ (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit)))) {
                vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0x19U;
                hbm_controller_tb_simple__DOT__dut__DOT__best_priority 
                    = (7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x69U] 
                             >> 9U));
                hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                    = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x68U] 
                                >> 1U));
                vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit 
                    = hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit;
            } else if (((IData)(hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit) 
                        & (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit))) {
                if (((7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x69U] 
                            >> 9U)) > (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_priority))) {
                    vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0x19U;
                    hbm_controller_tb_simple__DOT__dut__DOT__best_priority 
                        = (7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x69U] 
                                 >> 9U));
                    hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                        = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x68U] 
                                    >> 1U));
                } else if (((7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x69U] 
                                   >> 9U)) == (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_priority))) {
                    if (((0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x68U] 
                                   >> 1U)) < (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_age))) {
                        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0x19U;
                        hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                            = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x68U] 
                                        >> 1U));
                    }
                }
            } else if ((1U & ((~ (IData)(hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit)) 
                              & (~ (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit))))) {
                if (((7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x69U] 
                            >> 9U)) > (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_priority))) {
                    vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0x19U;
                    hbm_controller_tb_simple__DOT__dut__DOT__best_priority 
                        = (7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x69U] 
                                 >> 9U));
                    hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                        = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x68U] 
                                    >> 1U));
                } else if (((7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x69U] 
                                   >> 9U)) == (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_priority))) {
                    if (((0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x68U] 
                                   >> 1U)) < (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_age))) {
                        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0x19U;
                        hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                            = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x68U] 
                                        >> 1U));
                    }
                }
            }
        } else {
            vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0x19U;
            hbm_controller_tb_simple__DOT__dut__DOT__best_priority 
                = (7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x69U] 
                         >> 9U));
            hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x68U] 
                            >> 1U));
            vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit 
                = hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit;
            vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__grant_valid = 1U;
        }
    }
    hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit = 0U;
    if (((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x70U] 
          >> 6U) & (0U == (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__state)))) {
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
            = (0xfffffffffULL & (((QData)((IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x6fU])) 
                                  << 0x1eU) | ((QData)((IData)(
                                                               vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x6eU])) 
                                               >> 2U)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch 
            = (0x1fU & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                                >> 0x1eU)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bg 
            = (7U & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                             >> 0x1aU)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_pch 
            = (1U & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                             >> 0x17U)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bank 
            = (0xfU & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                               >> 0x16U)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_row 
            = (0xffffU & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                                  >> 6U)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__Vfuncout 
            = (((((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__row_open 
                   >> ([&]() {
                                    vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__ch 
                                        = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                    vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__Vfuncout 
                                        = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__ch;
                                }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__Vfuncout))) 
                  & ((IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_pch) 
                     == (1U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_pch_reg 
                               >> ([&]() {
                                            vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__ch 
                                                = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                            vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__Vfuncout 
                                                = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__ch;
                                        }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__Vfuncout)))))) 
                 & ((IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bg) 
                    == ((0x5fU >= (0x7fU & ((IData)(3U) 
                                            * VL_EXTEND_II(32,5, 
                                                           ([&]() {
                                                    vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__ch 
                                                        = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                                    vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__Vfuncout 
                                                        = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__ch;
                                                }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__Vfuncout))))))
                         ? (7U & VL_SEL_IWII(96, vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_bg_reg, 
                                             (0x7fU 
                                              & ((IData)(3U) 
                                                 * 
                                                 VL_EXTEND_II(32,5, 
                                                              ([&]() {
                                                        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__ch 
                                                            = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                                        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__Vfuncout 
                                                            = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__ch;
                                                    }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__Vfuncout))))), 3U))
                         : 0U))) & ((IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bank) 
                                    == (0xfU & VL_SEL_IWII(128, vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_bank_reg, 
                                                           (0x7fU 
                                                            & VL_SHIFTL_III(7,32,32, 
                                                                            VL_EXTEND_II(32,5, 
                                                                                ([&]() {
                                                vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__ch 
                                                    = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                                vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__Vfuncout 
                                                    = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__ch;
                                            }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__Vfuncout))), 2U)), 4U)))) 
               & ((IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_row) 
                  == (0xffffU & VL_SEL_IWII(512, vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_row_reg, 
                                            (0x1ffU 
                                             & VL_SHIFTL_III(9,32,32, 
                                                             VL_EXTEND_II(32,5, 
                                                                          ([&]() {
                                            vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__ch 
                                                = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                            vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__Vfuncout 
                                                = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__ch;
                                        }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__Vfuncout))), 4U)), 0x10U))));
        hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit 
            = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__Vfuncout;
        if (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__grant_valid) {
            if (((IData)(hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit) 
                 & (~ (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit)))) {
                vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0x1aU;
                hbm_controller_tb_simple__DOT__dut__DOT__best_priority 
                    = (7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x6dU] 
                             >> 0xeU));
                hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                    = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x6cU] 
                                >> 6U));
                vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit 
                    = hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit;
            } else if (((IData)(hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit) 
                        & (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit))) {
                if (((7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x6dU] 
                            >> 0xeU)) > (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_priority))) {
                    vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0x1aU;
                    hbm_controller_tb_simple__DOT__dut__DOT__best_priority 
                        = (7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x6dU] 
                                 >> 0xeU));
                    hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                        = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x6cU] 
                                    >> 6U));
                } else if (((7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x6dU] 
                                   >> 0xeU)) == (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_priority))) {
                    if (((0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x6cU] 
                                   >> 6U)) < (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_age))) {
                        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0x1aU;
                        hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                            = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x6cU] 
                                        >> 6U));
                    }
                }
            } else if ((1U & ((~ (IData)(hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit)) 
                              & (~ (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit))))) {
                if (((7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x6dU] 
                            >> 0xeU)) > (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_priority))) {
                    vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0x1aU;
                    hbm_controller_tb_simple__DOT__dut__DOT__best_priority 
                        = (7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x6dU] 
                                 >> 0xeU));
                    hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                        = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x6cU] 
                                    >> 6U));
                } else if (((7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x6dU] 
                                   >> 0xeU)) == (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_priority))) {
                    if (((0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x6cU] 
                                   >> 6U)) < (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_age))) {
                        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0x1aU;
                        hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                            = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x6cU] 
                                        >> 6U));
                    }
                }
            }
        } else {
            vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0x1aU;
            hbm_controller_tb_simple__DOT__dut__DOT__best_priority 
                = (7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x6dU] 
                         >> 0xeU));
            hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x6cU] 
                            >> 6U));
            vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit 
                = hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit;
            vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__grant_valid = 1U;
        }
    }
    hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit = 0U;
    if (((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x74U] 
          >> 0xbU) & (0U == (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__state)))) {
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
            = (0xfffffffffULL & (((QData)((IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x73U])) 
                                  << 0x19U) | ((QData)((IData)(
                                                               vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x72U])) 
                                               >> 7U)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch 
            = (0x1fU & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                                >> 0x1eU)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bg 
            = (7U & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                             >> 0x1aU)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_pch 
            = (1U & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                             >> 0x17U)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bank 
            = (0xfU & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                               >> 0x16U)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_row 
            = (0xffffU & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                                  >> 6U)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__Vfuncout 
            = (((((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__row_open 
                   >> ([&]() {
                                    vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__ch 
                                        = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                    vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__Vfuncout 
                                        = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__ch;
                                }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__Vfuncout))) 
                  & ((IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_pch) 
                     == (1U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_pch_reg 
                               >> ([&]() {
                                            vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__ch 
                                                = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                            vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__Vfuncout 
                                                = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__ch;
                                        }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__Vfuncout)))))) 
                 & ((IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bg) 
                    == ((0x5fU >= (0x7fU & ((IData)(3U) 
                                            * VL_EXTEND_II(32,5, 
                                                           ([&]() {
                                                    vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__ch 
                                                        = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                                    vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__Vfuncout 
                                                        = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__ch;
                                                }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__Vfuncout))))))
                         ? (7U & VL_SEL_IWII(96, vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_bg_reg, 
                                             (0x7fU 
                                              & ((IData)(3U) 
                                                 * 
                                                 VL_EXTEND_II(32,5, 
                                                              ([&]() {
                                                        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__ch 
                                                            = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                                        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__Vfuncout 
                                                            = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__ch;
                                                    }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__Vfuncout))))), 3U))
                         : 0U))) & ((IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bank) 
                                    == (0xfU & VL_SEL_IWII(128, vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_bank_reg, 
                                                           (0x7fU 
                                                            & VL_SHIFTL_III(7,32,32, 
                                                                            VL_EXTEND_II(32,5, 
                                                                                ([&]() {
                                                vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__ch 
                                                    = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                                vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__Vfuncout 
                                                    = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__ch;
                                            }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__Vfuncout))), 2U)), 4U)))) 
               & ((IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_row) 
                  == (0xffffU & VL_SEL_IWII(512, vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_row_reg, 
                                            (0x1ffU 
                                             & VL_SHIFTL_III(9,32,32, 
                                                             VL_EXTEND_II(32,5, 
                                                                          ([&]() {
                                            vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__ch 
                                                = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                            vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__Vfuncout 
                                                = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__ch;
                                        }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__Vfuncout))), 4U)), 0x10U))));
        hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit 
            = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__Vfuncout;
        if (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__grant_valid) {
            if (((IData)(hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit) 
                 & (~ (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit)))) {
                vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0x1bU;
                hbm_controller_tb_simple__DOT__dut__DOT__best_priority 
                    = (7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x71U] 
                             >> 0x13U));
                hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                    = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x70U] 
                                >> 0xbU));
                vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit 
                    = hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit;
            } else if (((IData)(hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit) 
                        & (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit))) {
                if (((7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x71U] 
                            >> 0x13U)) > (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_priority))) {
                    vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0x1bU;
                    hbm_controller_tb_simple__DOT__dut__DOT__best_priority 
                        = (7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x71U] 
                                 >> 0x13U));
                    hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                        = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x70U] 
                                    >> 0xbU));
                } else if (((7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x71U] 
                                   >> 0x13U)) == (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_priority))) {
                    if (((0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x70U] 
                                   >> 0xbU)) < (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_age))) {
                        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0x1bU;
                        hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                            = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x70U] 
                                        >> 0xbU));
                    }
                }
            } else if ((1U & ((~ (IData)(hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit)) 
                              & (~ (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit))))) {
                if (((7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x71U] 
                            >> 0x13U)) > (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_priority))) {
                    vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0x1bU;
                    hbm_controller_tb_simple__DOT__dut__DOT__best_priority 
                        = (7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x71U] 
                                 >> 0x13U));
                    hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                        = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x70U] 
                                    >> 0xbU));
                } else if (((7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x71U] 
                                   >> 0x13U)) == (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_priority))) {
                    if (((0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x70U] 
                                   >> 0xbU)) < (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_age))) {
                        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0x1bU;
                        hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                            = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x70U] 
                                        >> 0xbU));
                    }
                }
            }
        } else {
            vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0x1bU;
            hbm_controller_tb_simple__DOT__dut__DOT__best_priority 
                = (7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x71U] 
                         >> 0x13U));
            hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x70U] 
                            >> 0xbU));
            vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit 
                = hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit;
            vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__grant_valid = 1U;
        }
    }
    hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit = 0U;
    if (((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x78U] 
          >> 0x10U) & (0U == (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__state)))) {
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
            = (0xfffffffffULL & (((QData)((IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x77U])) 
                                  << 0x14U) | ((QData)((IData)(
                                                               vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x76U])) 
                                               >> 0xcU)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch 
            = (0x1fU & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                                >> 0x1eU)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bg 
            = (7U & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                             >> 0x1aU)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_pch 
            = (1U & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                             >> 0x17U)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bank 
            = (0xfU & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                               >> 0x16U)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_row 
            = (0xffffU & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                                  >> 6U)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__Vfuncout 
            = (((((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__row_open 
                   >> ([&]() {
                                    vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__ch 
                                        = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                    vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__Vfuncout 
                                        = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__ch;
                                }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__Vfuncout))) 
                  & ((IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_pch) 
                     == (1U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_pch_reg 
                               >> ([&]() {
                                            vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__ch 
                                                = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                            vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__Vfuncout 
                                                = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__ch;
                                        }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__Vfuncout)))))) 
                 & ((IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bg) 
                    == ((0x5fU >= (0x7fU & ((IData)(3U) 
                                            * VL_EXTEND_II(32,5, 
                                                           ([&]() {
                                                    vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__ch 
                                                        = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                                    vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__Vfuncout 
                                                        = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__ch;
                                                }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__Vfuncout))))))
                         ? (7U & VL_SEL_IWII(96, vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_bg_reg, 
                                             (0x7fU 
                                              & ((IData)(3U) 
                                                 * 
                                                 VL_EXTEND_II(32,5, 
                                                              ([&]() {
                                                        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__ch 
                                                            = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                                        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__Vfuncout 
                                                            = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__ch;
                                                    }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__Vfuncout))))), 3U))
                         : 0U))) & ((IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bank) 
                                    == (0xfU & VL_SEL_IWII(128, vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_bank_reg, 
                                                           (0x7fU 
                                                            & VL_SHIFTL_III(7,32,32, 
                                                                            VL_EXTEND_II(32,5, 
                                                                                ([&]() {
                                                vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__ch 
                                                    = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                                vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__Vfuncout 
                                                    = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__ch;
                                            }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__Vfuncout))), 2U)), 4U)))) 
               & ((IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_row) 
                  == (0xffffU & VL_SEL_IWII(512, vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_row_reg, 
                                            (0x1ffU 
                                             & VL_SHIFTL_III(9,32,32, 
                                                             VL_EXTEND_II(32,5, 
                                                                          ([&]() {
                                            vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__ch 
                                                = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                            vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__Vfuncout 
                                                = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__ch;
                                        }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__Vfuncout))), 4U)), 0x10U))));
        hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit 
            = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__Vfuncout;
        if (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__grant_valid) {
            if (((IData)(hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit) 
                 & (~ (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit)))) {
                vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0x1cU;
                hbm_controller_tb_simple__DOT__dut__DOT__best_priority 
                    = (7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x75U] 
                             >> 0x18U));
                hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                    = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x74U] 
                                >> 0x10U));
                vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit 
                    = hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit;
            } else if (((IData)(hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit) 
                        & (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit))) {
                if (((7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x75U] 
                            >> 0x18U)) > (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_priority))) {
                    vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0x1cU;
                    hbm_controller_tb_simple__DOT__dut__DOT__best_priority 
                        = (7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x75U] 
                                 >> 0x18U));
                    hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                        = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x74U] 
                                    >> 0x10U));
                } else if (((7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x75U] 
                                   >> 0x18U)) == (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_priority))) {
                    if (((0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x74U] 
                                   >> 0x10U)) < (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_age))) {
                        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0x1cU;
                        hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                            = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x74U] 
                                        >> 0x10U));
                    }
                }
            } else if ((1U & ((~ (IData)(hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit)) 
                              & (~ (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit))))) {
                if (((7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x75U] 
                            >> 0x18U)) > (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_priority))) {
                    vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0x1cU;
                    hbm_controller_tb_simple__DOT__dut__DOT__best_priority 
                        = (7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x75U] 
                                 >> 0x18U));
                    hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                        = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x74U] 
                                    >> 0x10U));
                } else if (((7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x75U] 
                                   >> 0x18U)) == (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_priority))) {
                    if (((0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x74U] 
                                   >> 0x10U)) < (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_age))) {
                        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0x1cU;
                        hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                            = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x74U] 
                                        >> 0x10U));
                    }
                }
            }
        } else {
            vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0x1cU;
            hbm_controller_tb_simple__DOT__dut__DOT__best_priority 
                = (7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x75U] 
                         >> 0x18U));
            hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x74U] 
                            >> 0x10U));
            vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit 
                = hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit;
            vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__grant_valid = 1U;
        }
    }
    hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit = 0U;
    if (((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x7cU] 
          >> 0x15U) & (0U == (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__state)))) {
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
            = (0xfffffffffULL & (((QData)((IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x7bU])) 
                                  << 0xfU) | ((QData)((IData)(
                                                              vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x7aU])) 
                                              >> 0x11U)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch 
            = (0x1fU & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                                >> 0x1eU)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bg 
            = (7U & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                             >> 0x1aU)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_pch 
            = (1U & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                             >> 0x17U)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bank 
            = (0xfU & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                               >> 0x16U)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_row 
            = (0xffffU & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                                  >> 6U)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__Vfuncout 
            = (((((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__row_open 
                   >> ([&]() {
                                    vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__ch 
                                        = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                    vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__Vfuncout 
                                        = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__ch;
                                }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__Vfuncout))) 
                  & ((IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_pch) 
                     == (1U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_pch_reg 
                               >> ([&]() {
                                            vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__ch 
                                                = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                            vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__Vfuncout 
                                                = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__ch;
                                        }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__Vfuncout)))))) 
                 & ((IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bg) 
                    == ((0x5fU >= (0x7fU & ((IData)(3U) 
                                            * VL_EXTEND_II(32,5, 
                                                           ([&]() {
                                                    vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__ch 
                                                        = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                                    vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__Vfuncout 
                                                        = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__ch;
                                                }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__Vfuncout))))))
                         ? (7U & VL_SEL_IWII(96, vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_bg_reg, 
                                             (0x7fU 
                                              & ((IData)(3U) 
                                                 * 
                                                 VL_EXTEND_II(32,5, 
                                                              ([&]() {
                                                        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__ch 
                                                            = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                                        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__Vfuncout 
                                                            = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__ch;
                                                    }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__Vfuncout))))), 3U))
                         : 0U))) & ((IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bank) 
                                    == (0xfU & VL_SEL_IWII(128, vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_bank_reg, 
                                                           (0x7fU 
                                                            & VL_SHIFTL_III(7,32,32, 
                                                                            VL_EXTEND_II(32,5, 
                                                                                ([&]() {
                                                vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__ch 
                                                    = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                                vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__Vfuncout 
                                                    = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__ch;
                                            }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__Vfuncout))), 2U)), 4U)))) 
               & ((IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_row) 
                  == (0xffffU & VL_SEL_IWII(512, vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_row_reg, 
                                            (0x1ffU 
                                             & VL_SHIFTL_III(9,32,32, 
                                                             VL_EXTEND_II(32,5, 
                                                                          ([&]() {
                                            vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__ch 
                                                = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                            vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__Vfuncout 
                                                = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__ch;
                                        }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__Vfuncout))), 4U)), 0x10U))));
        hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit 
            = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__Vfuncout;
        if (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__grant_valid) {
            if (((IData)(hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit) 
                 & (~ (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit)))) {
                vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0x1dU;
                hbm_controller_tb_simple__DOT__dut__DOT__best_priority 
                    = (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x79U] 
                       >> 0x1dU);
                hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                    = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x78U] 
                                >> 0x15U));
                vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit 
                    = hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit;
            } else if (((IData)(hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit) 
                        & (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit))) {
                if (((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x79U] 
                      >> 0x1dU) > (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_priority))) {
                    vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0x1dU;
                    hbm_controller_tb_simple__DOT__dut__DOT__best_priority 
                        = (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x79U] 
                           >> 0x1dU);
                    hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                        = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x78U] 
                                    >> 0x15U));
                } else if (((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x79U] 
                             >> 0x1dU) == (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_priority))) {
                    if (((0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x78U] 
                                   >> 0x15U)) < (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_age))) {
                        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0x1dU;
                        hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                            = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x78U] 
                                        >> 0x15U));
                    }
                }
            } else if ((1U & ((~ (IData)(hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit)) 
                              & (~ (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit))))) {
                if (((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x79U] 
                      >> 0x1dU) > (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_priority))) {
                    vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0x1dU;
                    hbm_controller_tb_simple__DOT__dut__DOT__best_priority 
                        = (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x79U] 
                           >> 0x1dU);
                    hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                        = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x78U] 
                                    >> 0x15U));
                } else if (((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x79U] 
                             >> 0x1dU) == (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_priority))) {
                    if (((0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x78U] 
                                   >> 0x15U)) < (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_age))) {
                        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0x1dU;
                        hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                            = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x78U] 
                                        >> 0x15U));
                    }
                }
            }
        } else {
            vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0x1dU;
            hbm_controller_tb_simple__DOT__dut__DOT__best_priority 
                = (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x79U] 
                   >> 0x1dU);
            hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                = (0xffU & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x78U] 
                            >> 0x15U));
            vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit 
                = hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit;
            vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__grant_valid = 1U;
        }
    }
    hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit = 0U;
    if (((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x80U] 
          >> 0x1aU) & (0U == (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__state)))) {
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
            = (0xfffffffffULL & (((QData)((IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x7fU])) 
                                  << 0xaU) | ((QData)((IData)(
                                                              vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x7eU])) 
                                              >> 0x16U)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch 
            = (0x1fU & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                                >> 0x1eU)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bg 
            = (7U & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                             >> 0x1aU)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_pch 
            = (1U & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                             >> 0x17U)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bank 
            = (0xfU & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                               >> 0x16U)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_row 
            = (0xffffU & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                                  >> 6U)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__Vfuncout 
            = (((((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__row_open 
                   >> ([&]() {
                                    vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__ch 
                                        = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                    vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__Vfuncout 
                                        = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__ch;
                                }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__Vfuncout))) 
                  & ((IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_pch) 
                     == (1U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_pch_reg 
                               >> ([&]() {
                                            vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__ch 
                                                = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                            vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__Vfuncout 
                                                = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__ch;
                                        }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__Vfuncout)))))) 
                 & ((IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bg) 
                    == ((0x5fU >= (0x7fU & ((IData)(3U) 
                                            * VL_EXTEND_II(32,5, 
                                                           ([&]() {
                                                    vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__ch 
                                                        = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                                    vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__Vfuncout 
                                                        = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__ch;
                                                }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__Vfuncout))))))
                         ? (7U & VL_SEL_IWII(96, vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_bg_reg, 
                                             (0x7fU 
                                              & ((IData)(3U) 
                                                 * 
                                                 VL_EXTEND_II(32,5, 
                                                              ([&]() {
                                                        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__ch 
                                                            = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                                        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__Vfuncout 
                                                            = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__ch;
                                                    }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__Vfuncout))))), 3U))
                         : 0U))) & ((IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bank) 
                                    == (0xfU & VL_SEL_IWII(128, vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_bank_reg, 
                                                           (0x7fU 
                                                            & VL_SHIFTL_III(7,32,32, 
                                                                            VL_EXTEND_II(32,5, 
                                                                                ([&]() {
                                                vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__ch 
                                                    = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                                vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__Vfuncout 
                                                    = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__ch;
                                            }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__Vfuncout))), 2U)), 4U)))) 
               & ((IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_row) 
                  == (0xffffU & VL_SEL_IWII(512, vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_row_reg, 
                                            (0x1ffU 
                                             & VL_SHIFTL_III(9,32,32, 
                                                             VL_EXTEND_II(32,5, 
                                                                          ([&]() {
                                            vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__ch 
                                                = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                            vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__Vfuncout 
                                                = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__ch;
                                        }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__Vfuncout))), 4U)), 0x10U))));
        hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit 
            = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__Vfuncout;
        if (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__grant_valid) {
            if (((IData)(hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit) 
                 & (~ (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit)))) {
                vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0x1eU;
                hbm_controller_tb_simple__DOT__dut__DOT__best_priority 
                    = (7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x7eU] 
                             >> 2U));
                hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                    = (0xffU & ((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x7dU] 
                                 << 6U) | (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x7cU] 
                                           >> 0x1aU)));
                vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit 
                    = hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit;
            } else if (((IData)(hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit) 
                        & (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit))) {
                if (((7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x7eU] 
                            >> 2U)) > (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_priority))) {
                    vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0x1eU;
                    hbm_controller_tb_simple__DOT__dut__DOT__best_priority 
                        = (7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x7eU] 
                                 >> 2U));
                    hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                        = (0xffU & ((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x7dU] 
                                     << 6U) | (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x7cU] 
                                               >> 0x1aU)));
                } else if (((7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x7eU] 
                                   >> 2U)) == (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_priority))) {
                    if (((0xffU & ((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x7dU] 
                                    << 6U) | (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x7cU] 
                                              >> 0x1aU))) 
                         < (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_age))) {
                        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0x1eU;
                        hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                            = (0xffU & ((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x7dU] 
                                         << 6U) | (
                                                   vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x7cU] 
                                                   >> 0x1aU)));
                    }
                }
            } else if ((1U & ((~ (IData)(hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit)) 
                              & (~ (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit))))) {
                if (((7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x7eU] 
                            >> 2U)) > (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_priority))) {
                    vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0x1eU;
                    hbm_controller_tb_simple__DOT__dut__DOT__best_priority 
                        = (7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x7eU] 
                                 >> 2U));
                    hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                        = (0xffU & ((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x7dU] 
                                     << 6U) | (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x7cU] 
                                               >> 0x1aU)));
                } else if (((7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x7eU] 
                                   >> 2U)) == (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_priority))) {
                    if (((0xffU & ((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x7dU] 
                                    << 6U) | (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x7cU] 
                                              >> 0x1aU))) 
                         < (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_age))) {
                        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0x1eU;
                        hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                            = (0xffU & ((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x7dU] 
                                         << 6U) | (
                                                   vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x7cU] 
                                                   >> 0x1aU)));
                    }
                }
            }
        } else {
            vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0x1eU;
            hbm_controller_tb_simple__DOT__dut__DOT__best_priority 
                = (7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x7eU] 
                         >> 2U));
            hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                = (0xffU & ((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x7dU] 
                             << 6U) | (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x7cU] 
                                       >> 0x1aU)));
            vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit 
                = hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit;
            vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__grant_valid = 1U;
        }
    }
    hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit = 0U;
    if (((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x84U] 
          >> 0x1fU) & (0U == (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__state)))) {
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
            = (0xfffffffffULL & (((QData)((IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x83U])) 
                                  << 5U) | ((QData)((IData)(
                                                            vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x82U])) 
                                            >> 0x1bU)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch 
            = (0x1fU & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                                >> 0x1eU)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bg 
            = (7U & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                             >> 0x1aU)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_pch 
            = (1U & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                             >> 0x17U)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bank 
            = (0xfU & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                               >> 0x16U)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_row 
            = (0xffffU & (IData)((vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr 
                                  >> 6U)));
        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__Vfuncout 
            = (((((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__row_open 
                   >> ([&]() {
                                    vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__ch 
                                        = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                    vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__Vfuncout 
                                        = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__ch;
                                }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__Vfuncout))) 
                  & ((IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_pch) 
                     == (1U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_pch_reg 
                               >> ([&]() {
                                            vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__ch 
                                                = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                            vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__Vfuncout 
                                                = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__ch;
                                        }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__Vfuncout)))))) 
                 & ((IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bg) 
                    == ((0x5fU >= (0x7fU & ((IData)(3U) 
                                            * VL_EXTEND_II(32,5, 
                                                           ([&]() {
                                                    vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__ch 
                                                        = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                                    vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__Vfuncout 
                                                        = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__ch;
                                                }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__Vfuncout))))))
                         ? (7U & VL_SEL_IWII(96, vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_bg_reg, 
                                             (0x7fU 
                                              & ((IData)(3U) 
                                                 * 
                                                 VL_EXTEND_II(32,5, 
                                                              ([&]() {
                                                        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__ch 
                                                            = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                                        vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__Vfuncout 
                                                            = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__ch;
                                                    }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__Vfuncout))))), 3U))
                         : 0U))) & ((IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bank) 
                                    == (0xfU & VL_SEL_IWII(128, vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_bank_reg, 
                                                           (0x7fU 
                                                            & VL_SHIFTL_III(7,32,32, 
                                                                            VL_EXTEND_II(32,5, 
                                                                                ([&]() {
                                                vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__ch 
                                                    = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                                vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__Vfuncout 
                                                    = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__ch;
                                            }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__Vfuncout))), 2U)), 4U)))) 
               & ((IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_row) 
                  == (0xffffU & VL_SEL_IWII(512, vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_row_reg, 
                                            (0x1ffU 
                                             & VL_SHIFTL_III(9,32,32, 
                                                             VL_EXTEND_II(32,5, 
                                                                          ([&]() {
                                            vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__ch 
                                                = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
                                            vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__Vfuncout 
                                                = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__ch;
                                        }(), (IData)(vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__Vfuncout))), 4U)), 0x10U))));
        hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit 
            = vlSelfRef.__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__Vfuncout;
        if (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__grant_valid) {
            if (((IData)(hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit) 
                 & (~ (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit)))) {
                vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0x1fU;
                hbm_controller_tb_simple__DOT__dut__DOT__best_priority 
                    = (7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x82U] 
                             >> 7U));
                hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                    = (0xffU & ((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x81U] 
                                 << 1U) | (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x80U] 
                                           >> 0x1fU)));
                vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit 
                    = hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit;
            } else if (((IData)(hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit) 
                        & (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit))) {
                if (((7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x82U] 
                            >> 7U)) > (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_priority))) {
                    vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0x1fU;
                    hbm_controller_tb_simple__DOT__dut__DOT__best_priority 
                        = (7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x82U] 
                                 >> 7U));
                    hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                        = (0xffU & ((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x81U] 
                                     << 1U) | (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x80U] 
                                               >> 0x1fU)));
                } else if (((7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x82U] 
                                   >> 7U)) == (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_priority))) {
                    if (((0xffU & ((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x81U] 
                                    << 1U) | (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x80U] 
                                              >> 0x1fU))) 
                         < (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_age))) {
                        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0x1fU;
                        hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                            = (0xffU & ((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x81U] 
                                         << 1U) | (
                                                   vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x80U] 
                                                   >> 0x1fU)));
                    }
                }
            } else if ((1U & ((~ (IData)(hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit)) 
                              & (~ (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit))))) {
                if (((7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x82U] 
                            >> 7U)) > (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_priority))) {
                    vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0x1fU;
                    hbm_controller_tb_simple__DOT__dut__DOT__best_priority 
                        = (7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x82U] 
                                 >> 7U));
                    hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                        = (0xffU & ((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x81U] 
                                     << 1U) | (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x80U] 
                                               >> 0x1fU)));
                } else if (((7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x82U] 
                                   >> 7U)) == (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_priority))) {
                    if (((0xffU & ((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x81U] 
                                    << 1U) | (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x80U] 
                                              >> 0x1fU))) 
                         < (IData)(hbm_controller_tb_simple__DOT__dut__DOT__best_age))) {
                        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0x1fU;
                        hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                            = (0xffU & ((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x81U] 
                                         << 1U) | (
                                                   vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x80U] 
                                                   >> 0x1fU)));
                    }
                }
            }
        } else {
            vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx = 0x1fU;
            hbm_controller_tb_simple__DOT__dut__DOT__best_priority 
                = (7U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x82U] 
                         >> 7U));
            hbm_controller_tb_simple__DOT__dut__DOT__best_age 
                = (0xffU & ((vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x81U] 
                             << 1U) | (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x80U] 
                                       >> 0x1fU)));
            vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit 
                = hbm_controller_tb_simple__DOT__dut__DOT__unnamedblk2__DOT__unnamedblk3__DOT__row_hit;
            vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__grant_valid = 1U;
        }
    }
    __Vtableidx1 = ((((IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__grant_row_hit) 
                      << 7U) | ((0U == (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__state)) 
                                << 6U)) | (((IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__grant_valid) 
                                            << 5U) 
                                           | (((IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__grant_rd_wr_n) 
                                               << 4U) 
                                              | (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__state))));
    vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__next_state 
        = Vhbm_controller_tb_simple__ConstPool__TABLE_hea14f260_0
        [__Vtableidx1];
}

VL_ATTR_COLD void Vhbm_controller_tb_simple___024root___eval_triggers__stl(Vhbm_controller_tb_simple___024root* vlSelf);

VL_ATTR_COLD bool Vhbm_controller_tb_simple___024root___eval_phase__stl(Vhbm_controller_tb_simple___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vhbm_controller_tb_simple___024root___eval_phase__stl\n"); );
    Vhbm_controller_tb_simple__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Init
    CData/*0:0*/ __VstlExecute;
    // Body
    Vhbm_controller_tb_simple___024root___eval_triggers__stl(vlSelf);
    __VstlExecute = vlSelfRef.__VstlTriggered.any();
    if (__VstlExecute) {
        Vhbm_controller_tb_simple___024root___eval_stl(vlSelf);
    }
    return (__VstlExecute);
}

#ifdef VL_DEBUG
VL_ATTR_COLD void Vhbm_controller_tb_simple___024root___dump_triggers__act(Vhbm_controller_tb_simple___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vhbm_controller_tb_simple___024root___dump_triggers__act\n"); );
    Vhbm_controller_tb_simple__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    if ((1U & (~ vlSelfRef.__VactTriggered.any()))) {
        VL_DBG_MSGF("         No triggers active\n");
    }
    if ((1ULL & vlSelfRef.__VactTriggered.word(0U))) {
        VL_DBG_MSGF("         'act' region trigger index 0 is active: @(posedge clk)\n");
    }
    if ((2ULL & vlSelfRef.__VactTriggered.word(0U))) {
        VL_DBG_MSGF("         'act' region trigger index 1 is active: @(negedge hbm_controller_tb_simple.rst_n)\n");
    }
}
#endif  // VL_DEBUG

#ifdef VL_DEBUG
VL_ATTR_COLD void Vhbm_controller_tb_simple___024root___dump_triggers__nba(Vhbm_controller_tb_simple___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vhbm_controller_tb_simple___024root___dump_triggers__nba\n"); );
    Vhbm_controller_tb_simple__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    if ((1U & (~ vlSelfRef.__VnbaTriggered.any()))) {
        VL_DBG_MSGF("         No triggers active\n");
    }
    if ((1ULL & vlSelfRef.__VnbaTriggered.word(0U))) {
        VL_DBG_MSGF("         'nba' region trigger index 0 is active: @(posedge clk)\n");
    }
    if ((2ULL & vlSelfRef.__VnbaTriggered.word(0U))) {
        VL_DBG_MSGF("         'nba' region trigger index 1 is active: @(negedge hbm_controller_tb_simple.rst_n)\n");
    }
}
#endif  // VL_DEBUG

VL_ATTR_COLD void Vhbm_controller_tb_simple___024root___ctor_var_reset(Vhbm_controller_tb_simple___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vhbm_controller_tb_simple___024root___ctor_var_reset\n"); );
    Vhbm_controller_tb_simple__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    vlSelf->clk = VL_RAND_RESET_I(1);
    vlSelf->hbm_controller_tb_simple__DOT__rst_n = VL_RAND_RESET_I(1);
    vlSelf->hbm_controller_tb_simple__DOT__tb_req_valid = VL_RAND_RESET_I(1);
    vlSelf->hbm_controller_tb_simple__DOT__tb_req_id = VL_RAND_RESET_I(32);
    vlSelf->hbm_controller_tb_simple__DOT__tb_req_addr = VL_RAND_RESET_Q(36);
    vlSelf->hbm_controller_tb_simple__DOT__tb_req_rd_wr_n = VL_RAND_RESET_I(1);
    vlSelf->hbm_controller_tb_simple__DOT__tb_req_ready = VL_RAND_RESET_I(1);
    vlSelf->hbm_controller_tb_simple__DOT__tb_resp_valid = VL_RAND_RESET_I(1);
    vlSelf->hbm_controller_tb_simple__DOT__tb_resp_id = VL_RAND_RESET_I(32);
    vlSelf->hbm_controller_tb_simple__DOT__tb_resp_success = VL_RAND_RESET_I(1);
    vlSelf->hbm_controller_tb_simple__DOT__tb_resp_status = VL_RAND_RESET_I(8);
    vlSelf->hbm_controller_tb_simple__DOT__tb_dram_cmd = VL_RAND_RESET_I(4);
    vlSelf->hbm_controller_tb_simple__DOT__tb_stat_requests = VL_RAND_RESET_I(32);
    vlSelf->hbm_controller_tb_simple__DOT__tb_stat_completed = VL_RAND_RESET_I(32);
    vlSelf->hbm_controller_tb_simple__DOT__tb_stat_hit_rate = VL_RAND_RESET_I(8);
    vlSelf->hbm_controller_tb_simple__DOT__cycle = VL_RAND_RESET_I(32);
    vlSelf->hbm_controller_tb_simple__DOT__resp_count = VL_RAND_RESET_I(32);
    VL_RAND_RESET_W(4256, vlSelf->hbm_controller_tb_simple__DOT__dut__DOT__queue);
    vlSelf->hbm_controller_tb_simple__DOT__dut__DOT__enq_ptr = VL_RAND_RESET_I(5);
    vlSelf->hbm_controller_tb_simple__DOT__dut__DOT__queue_count = VL_RAND_RESET_I(6);
    vlSelf->hbm_controller_tb_simple__DOT__dut__DOT__age_counter = VL_RAND_RESET_I(8);
    vlSelf->hbm_controller_tb_simple__DOT__dut__DOT__queue_empty = VL_RAND_RESET_I(1);
    vlSelf->hbm_controller_tb_simple__DOT__dut__DOT__row_open = VL_RAND_RESET_I(32);
    vlSelf->hbm_controller_tb_simple__DOT__dut__DOT__open_pch_reg = VL_RAND_RESET_I(32);
    VL_RAND_RESET_W(96, vlSelf->hbm_controller_tb_simple__DOT__dut__DOT__open_bg_reg);
    VL_RAND_RESET_W(128, vlSelf->hbm_controller_tb_simple__DOT__dut__DOT__open_bank_reg);
    VL_RAND_RESET_W(512, vlSelf->hbm_controller_tb_simple__DOT__dut__DOT__open_row_reg);
    vlSelf->hbm_controller_tb_simple__DOT__dut__DOT__best_idx = VL_RAND_RESET_I(5);
    vlSelf->hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit = VL_RAND_RESET_I(1);
    vlSelf->hbm_controller_tb_simple__DOT__dut__DOT__grant_valid = VL_RAND_RESET_I(1);
    vlSelf->hbm_controller_tb_simple__DOT__dut__DOT__grant_idx = VL_RAND_RESET_I(5);
    vlSelf->hbm_controller_tb_simple__DOT__dut__DOT__grant_row_hit = VL_RAND_RESET_I(1);
    vlSelf->hbm_controller_tb_simple__DOT__dut__DOT__grant_rd_wr_n = VL_RAND_RESET_I(1);
    vlSelf->hbm_controller_tb_simple__DOT__dut__DOT__state = VL_RAND_RESET_I(4);
    vlSelf->hbm_controller_tb_simple__DOT__dut__DOT__next_state = VL_RAND_RESET_I(4);
    vlSelf->hbm_controller_tb_simple__DOT__dut__DOT__txn_started = VL_RAND_RESET_I(1);
    vlSelf->hbm_controller_tb_simple__DOT__dut__DOT__cur_id = VL_RAND_RESET_I(32);
    vlSelf->hbm_controller_tb_simple__DOT__dut__DOT__resp_issued = VL_RAND_RESET_I(1);
    vlSelf->hbm_controller_tb_simple__DOT__dut__DOT__requests_q = VL_RAND_RESET_I(32);
    vlSelf->hbm_controller_tb_simple__DOT__dut__DOT__completed_q = VL_RAND_RESET_I(32);
    vlSelf->hbm_controller_tb_simple__DOT__dut__DOT____Vlvbound_h99c89ea2__0 = VL_RAND_RESET_I(1);
    vlSelf->hbm_controller_tb_simple__DOT__dut__DOT____Vlvbound_h71839dcf__0 = VL_RAND_RESET_I(32);
    vlSelf->hbm_controller_tb_simple__DOT__dut__DOT____Vlvbound_h822848eb__0 = VL_RAND_RESET_Q(36);
    vlSelf->hbm_controller_tb_simple__DOT__dut__DOT____Vlvbound_h2ff16325__0 = VL_RAND_RESET_I(1);
    vlSelf->hbm_controller_tb_simple__DOT__dut__DOT____Vlvbound_h33e97cea__0 = VL_RAND_RESET_I(16);
    vlSelf->hbm_controller_tb_simple__DOT__dut__DOT____Vlvbound_h2e975fa7__0 = VL_RAND_RESET_I(3);
    vlSelf->hbm_controller_tb_simple__DOT__dut__DOT____Vlvbound_h28b1ddf3__0 = VL_RAND_RESET_I(8);
    vlSelf->hbm_controller_tb_simple__DOT__dut__DOT____Vlvbound_hb59a37e4__0 = VL_RAND_RESET_I(4);
    vlSelf->hbm_controller_tb_simple__DOT__dut__DOT____Vlvbound_h26d43ea3__0 = VL_RAND_RESET_I(5);
    vlSelf->hbm_controller_tb_simple__DOT__dut__DOT____Vlvbound_h31965574__0 = VL_RAND_RESET_I(4);
    vlSelf->hbm_controller_tb_simple__DOT__dut__DOT____Vlvbound_h2f30f8cf__0 = VL_RAND_RESET_I(16);
    vlSelf->hbm_controller_tb_simple__DOT__dut__DOT____Vlvbound_h2e8529d8__0 = VL_RAND_RESET_I(2);
    vlSelf->hbm_controller_tb_simple__DOT__dut__DOT____Vlvbound_h989f323f__0 = VL_RAND_RESET_I(1);
    vlSelf->hbm_controller_tb_simple__DOT__dut__DOT____Vlvbound_h7936eb07__0 = VL_RAND_RESET_I(3);
    vlSelf->hbm_controller_tb_simple__DOT__dut__DOT____Vlvbound_hb8feabb2__0 = VL_RAND_RESET_I(1);
    vlSelf->__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__Vfuncout = VL_RAND_RESET_I(1);
    vlSelf->__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr = VL_RAND_RESET_Q(36);
    vlSelf->__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch = VL_RAND_RESET_I(5);
    vlSelf->__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_pch = VL_RAND_RESET_I(1);
    vlSelf->__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bg = VL_RAND_RESET_I(3);
    vlSelf->__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bank = VL_RAND_RESET_I(4);
    vlSelf->__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_row = VL_RAND_RESET_I(16);
    vlSelf->__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__Vfuncout = VL_RAND_RESET_I(5);
    vlSelf->__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__ch = VL_RAND_RESET_I(5);
    vlSelf->__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__Vfuncout = VL_RAND_RESET_I(5);
    vlSelf->__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__ch = VL_RAND_RESET_I(5);
    vlSelf->__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__Vfuncout = VL_RAND_RESET_I(5);
    vlSelf->__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__ch = VL_RAND_RESET_I(5);
    vlSelf->__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__Vfuncout = VL_RAND_RESET_I(5);
    vlSelf->__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__ch = VL_RAND_RESET_I(5);
    vlSelf->__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__Vfuncout = VL_RAND_RESET_I(5);
    vlSelf->__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__ch = VL_RAND_RESET_I(5);
    vlSelf->__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__Vfuncout = VL_RAND_RESET_I(5);
    vlSelf->__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__ch = VL_RAND_RESET_I(5);
    vlSelf->__Vdly__hbm_controller_tb_simple__DOT__tb_req_valid = VL_RAND_RESET_I(1);
    vlSelf->__Vdly__hbm_controller_tb_simple__DOT__rst_n = VL_RAND_RESET_I(1);
    vlSelf->__Vdly__hbm_controller_tb_simple__DOT__dut__DOT__queue_count = VL_RAND_RESET_I(6);
    vlSelf->__Vdly__hbm_controller_tb_simple__DOT__dut__DOT__cur_id = VL_RAND_RESET_I(32);
    vlSelf->__Vdly__hbm_controller_tb_simple__DOT__dut__DOT__resp_issued = VL_RAND_RESET_I(1);
    vlSelf->__Vdly__hbm_controller_tb_simple__DOT__dut__DOT__requests_q = VL_RAND_RESET_I(32);
    vlSelf->__Vdly__hbm_controller_tb_simple__DOT__dut__DOT__completed_q = VL_RAND_RESET_I(32);
    vlSelf->__Vtrigprevexpr___TOP__clk__0 = VL_RAND_RESET_I(1);
    vlSelf->__Vtrigprevexpr___TOP__hbm_controller_tb_simple__DOT__rst_n__0 = VL_RAND_RESET_I(1);
}
