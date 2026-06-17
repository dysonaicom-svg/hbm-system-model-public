// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design implementation internals
// See Vhbm_controller_tb_simple.h for the primary calling header

#include "Vhbm_controller_tb_simple__pch.h"
#include "Vhbm_controller_tb_simple___024root.h"

void Vhbm_controller_tb_simple___024root___eval_act(Vhbm_controller_tb_simple___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vhbm_controller_tb_simple___024root___eval_act\n"); );
    Vhbm_controller_tb_simple__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
}

void Vhbm_controller_tb_simple___024root___nba_sequent__TOP__0(Vhbm_controller_tb_simple___024root* vlSelf);
void Vhbm_controller_tb_simple___024root___nba_sequent__TOP__1(Vhbm_controller_tb_simple___024root* vlSelf);
void Vhbm_controller_tb_simple___024root___nba_sequent__TOP__2(Vhbm_controller_tb_simple___024root* vlSelf);
void Vhbm_controller_tb_simple___024root___nba_sequent__TOP__3(Vhbm_controller_tb_simple___024root* vlSelf);

void Vhbm_controller_tb_simple___024root___eval_nba(Vhbm_controller_tb_simple___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vhbm_controller_tb_simple___024root___eval_nba\n"); );
    Vhbm_controller_tb_simple__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    if ((3ULL & vlSelfRef.__VnbaTriggered.word(0U))) {
        Vhbm_controller_tb_simple___024root___nba_sequent__TOP__0(vlSelf);
    }
    if ((1ULL & vlSelfRef.__VnbaTriggered.word(0U))) {
        Vhbm_controller_tb_simple___024root___nba_sequent__TOP__1(vlSelf);
    }
    if ((3ULL & vlSelfRef.__VnbaTriggered.word(0U))) {
        Vhbm_controller_tb_simple___024root___nba_sequent__TOP__2(vlSelf);
    }
    if ((1ULL & vlSelfRef.__VnbaTriggered.word(0U))) {
        Vhbm_controller_tb_simple___024root___nba_sequent__TOP__3(vlSelf);
    }
}

extern const VlWide<16>/*511:0*/ Vhbm_controller_tb_simple__ConstPool__CONST_h93e1b771_0;

VL_INLINE_OPT void Vhbm_controller_tb_simple___024root___nba_sequent__TOP__0(Vhbm_controller_tb_simple___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vhbm_controller_tb_simple___024root___nba_sequent__TOP__0\n"); );
    Vhbm_controller_tb_simple__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Init
    CData/*4:0*/ __Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__0__Vfuncout;
    __Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__0__Vfuncout = 0;
    CData/*4:0*/ __Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__0__ch;
    __Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__0__ch = 0;
    CData/*4:0*/ __Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__1__Vfuncout;
    __Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__1__Vfuncout = 0;
    CData/*4:0*/ __Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__1__ch;
    __Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__1__ch = 0;
    CData/*4:0*/ __Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__2__Vfuncout;
    __Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__2__Vfuncout = 0;
    CData/*4:0*/ __Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__2__ch;
    __Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__2__ch = 0;
    CData/*4:0*/ __Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__3__Vfuncout;
    __Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__3__Vfuncout = 0;
    CData/*4:0*/ __Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__3__ch;
    __Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__3__ch = 0;
    CData/*4:0*/ __Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__4__Vfuncout;
    __Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__4__Vfuncout = 0;
    CData/*4:0*/ __Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__4__ch;
    __Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__4__ch = 0;
    CData/*4:0*/ __Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__5__Vfuncout;
    __Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__5__Vfuncout = 0;
    CData/*4:0*/ __Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__5__ch;
    __Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__5__ch = 0;
    CData/*4:0*/ __Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__6__Vfuncout;
    __Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__6__Vfuncout = 0;
    CData/*4:0*/ __Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__6__ch;
    __Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__6__ch = 0;
    CData/*4:0*/ __Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__7__Vfuncout;
    __Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__7__Vfuncout = 0;
    CData/*4:0*/ __Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__7__ch;
    __Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__7__ch = 0;
    CData/*4:0*/ __Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__8__Vfuncout;
    __Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__8__Vfuncout = 0;
    CData/*4:0*/ __Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__8__ch;
    __Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__8__ch = 0;
    CData/*4:0*/ __Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__9__Vfuncout;
    __Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__9__Vfuncout = 0;
    CData/*4:0*/ __Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__9__ch;
    __Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__9__ch = 0;
    CData/*4:0*/ __Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__10__Vfuncout;
    __Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__10__Vfuncout = 0;
    CData/*4:0*/ __Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__10__ch;
    __Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__10__ch = 0;
    CData/*4:0*/ __Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__11__Vfuncout;
    __Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__11__Vfuncout = 0;
    CData/*4:0*/ __Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__11__ch;
    __Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__11__ch = 0;
    CData/*4:0*/ __Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__12__Vfuncout;
    __Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__12__Vfuncout = 0;
    CData/*4:0*/ __Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__12__ch;
    __Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__12__ch = 0;
    CData/*4:0*/ __Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__13__Vfuncout;
    __Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__13__Vfuncout = 0;
    CData/*4:0*/ __Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__13__ch;
    __Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__13__ch = 0;
    CData/*4:0*/ __Vdly__hbm_controller_tb_simple__DOT__dut__DOT__enq_ptr;
    __Vdly__hbm_controller_tb_simple__DOT__dut__DOT__enq_ptr = 0;
    CData/*7:0*/ __Vdly__hbm_controller_tb_simple__DOT__dut__DOT__age_counter;
    __Vdly__hbm_controller_tb_simple__DOT__dut__DOT__age_counter = 0;
    IData/*31:0*/ __Vdly__hbm_controller_tb_simple__DOT__dut__DOT__open_pch_reg;
    __Vdly__hbm_controller_tb_simple__DOT__dut__DOT__open_pch_reg = 0;
    VlWide<3>/*95:0*/ __Vdly__hbm_controller_tb_simple__DOT__dut__DOT__open_bg_reg;
    VL_ZERO_W(96, __Vdly__hbm_controller_tb_simple__DOT__dut__DOT__open_bg_reg);
    VlWide<4>/*127:0*/ __Vdly__hbm_controller_tb_simple__DOT__dut__DOT__open_bank_reg;
    VL_ZERO_W(128, __Vdly__hbm_controller_tb_simple__DOT__dut__DOT__open_bank_reg);
    // Body
    __Vdly__hbm_controller_tb_simple__DOT__dut__DOT__age_counter 
        = vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__age_counter;
    __Vdly__hbm_controller_tb_simple__DOT__dut__DOT__enq_ptr 
        = vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__enq_ptr;
    vlSelfRef.__Vdly__hbm_controller_tb_simple__DOT__dut__DOT__queue_count 
        = vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue_count;
    vlSelfRef.__Vdly__hbm_controller_tb_simple__DOT__dut__DOT__resp_issued 
        = vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__resp_issued;
    vlSelfRef.__Vdly__hbm_controller_tb_simple__DOT__dut__DOT__requests_q 
        = vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__requests_q;
    vlSelfRef.__Vdly__hbm_controller_tb_simple__DOT__dut__DOT__completed_q 
        = vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__completed_q;
    __Vdly__hbm_controller_tb_simple__DOT__dut__DOT__open_pch_reg 
        = vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_pch_reg;
    __Vdly__hbm_controller_tb_simple__DOT__dut__DOT__open_bg_reg[0U] 
        = vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_bg_reg[0U];
    __Vdly__hbm_controller_tb_simple__DOT__dut__DOT__open_bg_reg[1U] 
        = vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_bg_reg[1U];
    __Vdly__hbm_controller_tb_simple__DOT__dut__DOT__open_bg_reg[2U] 
        = vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_bg_reg[2U];
    __Vdly__hbm_controller_tb_simple__DOT__dut__DOT__open_bank_reg[0U] 
        = vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_bank_reg[0U];
    __Vdly__hbm_controller_tb_simple__DOT__dut__DOT__open_bank_reg[1U] 
        = vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_bank_reg[1U];
    __Vdly__hbm_controller_tb_simple__DOT__dut__DOT__open_bank_reg[2U] 
        = vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_bank_reg[2U];
    __Vdly__hbm_controller_tb_simple__DOT__dut__DOT__open_bank_reg[3U] 
        = vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_bank_reg[3U];
    vlSelfRef.__Vdly__hbm_controller_tb_simple__DOT__dut__DOT__cur_id 
        = vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__cur_id;
    if (vlSelfRef.hbm_controller_tb_simple__DOT__rst_n) {
        __Vdly__hbm_controller_tb_simple__DOT__dut__DOT__age_counter 
            = ((0xffU == (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__age_counter))
                ? 0U : (0xffU & ((IData)(1U) + (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__age_counter))));
        if ((1U & (~ (((IData)(vlSelfRef.hbm_controller_tb_simple__DOT__tb_req_valid) 
                       & (0x20U > (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue_count))) 
                      & (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__grant_valid))))) {
            if (((IData)(vlSelfRef.hbm_controller_tb_simple__DOT__tb_req_valid) 
                 & (0x20U > (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue_count)))) {
                __Vdly__hbm_controller_tb_simple__DOT__dut__DOT__enq_ptr 
                    = (0x1fU & ((IData)(1U) + (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__enq_ptr)));
            }
        }
        if (((IData)(vlSelfRef.hbm_controller_tb_simple__DOT__tb_req_valid) 
             & (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__tb_req_ready))) {
            if ((0x20U > (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue_count))) {
                vlSelfRef.__Vdly__hbm_controller_tb_simple__DOT__dut__DOT__queue_count 
                    = (0x3fU & ((IData)(1U) + (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue_count)));
            }
        }
        if (((IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__grant_valid) 
             & (~ (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue_empty)))) {
            if ((0U < (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue_count))) {
                vlSelfRef.__Vdly__hbm_controller_tb_simple__DOT__dut__DOT__queue_count 
                    = (0x3fU & ((IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue_count) 
                                - (IData)(1U)));
            }
        }
        if ((((IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__grant_valid) 
              & (0U == (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__state))) 
             & (~ (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__txn_started)))) {
            vlSelfRef.__Vdly__hbm_controller_tb_simple__DOT__dut__DOT__cur_id 
                = ((0x109fU >= ((IData)(0x64U) + (0x1fffU 
                                                  & ((IData)(0x85U) 
                                                     * (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__grant_idx)))))
                    ? (((0U == (0x1fU & ((IData)(0x64U) 
                                         + (0x1fffU 
                                            & ((IData)(0x85U) 
                                               * (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__grant_idx))))))
                         ? 0U : (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[
                                 (((IData)(0x83U) + 
                                   (0x1fffU & ((IData)(0x85U) 
                                               * (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__grant_idx)))) 
                                  >> 5U)] << ((IData)(0x20U) 
                                              - (0x1fU 
                                                 & ((IData)(0x64U) 
                                                    + 
                                                    (0x1fffU 
                                                     & ((IData)(0x85U) 
                                                        * (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__grant_idx)))))))) 
                       | (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[
                          (((IData)(0x64U) + (0x1fffU 
                                              & ((IData)(0x85U) 
                                                 * (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__grant_idx)))) 
                           >> 5U)] >> (0x1fU & ((IData)(0x64U) 
                                                + (0x1fffU 
                                                   & ((IData)(0x85U) 
                                                      * (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__grant_idx)))))))
                    : 0U);
            vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__txn_started = 1U;
        }
        if (vlSelfRef.hbm_controller_tb_simple__DOT__tb_resp_valid) {
            vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__txn_started = 0U;
        }
        if (((IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__grant_valid) 
             & (0U == (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__state)))) {
            vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__grant_row_hit 
                = vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit;
            vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__grant_rd_wr_n 
                = ((0x109fU >= ((IData)(0x3fU) + (0x1fffU 
                                                  & ((IData)(0x85U) 
                                                     * (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx))))) 
                   && (1U & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[
                             (((IData)(0x3fU) + (0x1fffU 
                                                 & ((IData)(0x85U) 
                                                    * (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx)))) 
                              >> 5U)] >> (0x1fU & ((IData)(0x3fU) 
                                                   + 
                                                   (0x1fffU 
                                                    & ((IData)(0x85U) 
                                                       * (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx))))))));
        }
        if (((IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__grant_valid) 
             & (0U == (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__state)))) {
            vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT____Vlvbound_hb8feabb2__0 = 0U;
            if ((0x109fU >= ((IData)(0x84U) + (0x1fffU 
                                               & ((IData)(0x85U) 
                                                  * (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__grant_idx)))))) {
                vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[(
                                                                          ((IData)(0x84U) 
                                                                           + 
                                                                           (0x1fffU 
                                                                            & ((IData)(0x85U) 
                                                                               * (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__grant_idx)))) 
                                                                          >> 5U)] 
                    = (((~ ((IData)(1U) << (0x1fU & 
                                            ((IData)(0x84U) 
                                             + (0x1fffU 
                                                & ((IData)(0x85U) 
                                                   * (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__grant_idx))))))) 
                        & vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[
                        (((IData)(0x84U) + (0x1fffU 
                                            & ((IData)(0x85U) 
                                               * (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__grant_idx)))) 
                         >> 5U)]) | ((IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT____Vlvbound_hb8feabb2__0) 
                                     << (0x1fU & ((IData)(0x84U) 
                                                  + 
                                                  (0x1fffU 
                                                   & ((IData)(0x85U) 
                                                      * (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__grant_idx)))))));
            }
        }
    } else {
        __Vdly__hbm_controller_tb_simple__DOT__dut__DOT__age_counter = 0U;
        __Vdly__hbm_controller_tb_simple__DOT__dut__DOT__enq_ptr = 0U;
        vlSelfRef.__Vdly__hbm_controller_tb_simple__DOT__dut__DOT__queue_count = 0U;
        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__txn_started = 0U;
        vlSelfRef.__Vdly__hbm_controller_tb_simple__DOT__dut__DOT__cur_id = 0U;
        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__grant_row_hit = 0U;
        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__grant_rd_wr_n = 1U;
        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[4U] 
            = (0xffffffefU & vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[4U]);
        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[8U] 
            = (0xfffffdffU & vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[8U]);
        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0xcU] 
            = (0xffffbfffU & vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0xcU]);
        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x10U] 
            = (0xfff7ffffU & vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x10U]);
        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x14U] 
            = (0xfeffffffU & vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x14U]);
        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x18U] 
            = (0xdfffffffU & vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x18U]);
        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x1dU] 
            = (0xfffffffbU & vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x1dU]);
        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x21U] 
            = (0xffffff7fU & vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x21U]);
        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x25U] 
            = (0xffffefffU & vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x25U]);
        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x29U] 
            = (0xfffdffffU & vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x29U]);
        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x2dU] 
            = (0xffbfffffU & vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x2dU]);
        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x31U] 
            = (0xf7ffffffU & vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x31U]);
        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x36U] 
            = (0xfffffffeU & vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x36U]);
        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x3aU] 
            = (0xffffffdfU & vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x3aU]);
        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x3eU] 
            = (0xfffffbffU & vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x3eU]);
        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x42U] 
            = (0xffff7fffU & vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x42U]);
        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x46U] 
            = (0xffefffffU & vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x46U]);
        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x4aU] 
            = (0xfdffffffU & vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x4aU]);
        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x4eU] 
            = (0xbfffffffU & vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x4eU]);
        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x53U] 
            = (0xfffffff7U & vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x53U]);
        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x57U] 
            = (0xfffffeffU & vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x57U]);
        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x5bU] 
            = (0xffffdfffU & vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x5bU]);
        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x5fU] 
            = (0xfffbffffU & vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x5fU]);
        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x63U] 
            = (0xff7fffffU & vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x63U]);
        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x67U] 
            = (0xefffffffU & vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x67U]);
        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x6cU] 
            = (0xfffffffdU & vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x6cU]);
        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x70U] 
            = (0xffffffbfU & vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x70U]);
        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x74U] 
            = (0xfffff7ffU & vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x74U]);
        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x78U] 
            = (0xfffeffffU & vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x78U]);
        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x7cU] 
            = (0xffdfffffU & vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x7cU]);
        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x80U] 
            = (0xfbffffffU & vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x80U]);
        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x84U] 
            = (0x7fffffffU & vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x84U]);
    }
    if (vlSelfRef.hbm_controller_tb_simple__DOT__rst_n) {
        if (((IData)(vlSelfRef.hbm_controller_tb_simple__DOT__tb_req_valid) 
             & (0x20U > (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue_count)))) {
            vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT____Vlvbound_h99c89ea2__0 = 1U;
            if ((0x109fU >= ((IData)(0x84U) + (0x1fffU 
                                               & ((IData)(0x85U) 
                                                  * (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__enq_ptr)))))) {
                vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[(
                                                                          ((IData)(0x84U) 
                                                                           + 
                                                                           (0x1fffU 
                                                                            & ((IData)(0x85U) 
                                                                               * (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__enq_ptr)))) 
                                                                          >> 5U)] 
                    = (((~ ((IData)(1U) << (0x1fU & 
                                            ((IData)(0x84U) 
                                             + (0x1fffU 
                                                & ((IData)(0x85U) 
                                                   * (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__enq_ptr))))))) 
                        & vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[
                        (((IData)(0x84U) + (0x1fffU 
                                            & ((IData)(0x85U) 
                                               * (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__enq_ptr)))) 
                         >> 5U)]) | ((IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT____Vlvbound_h99c89ea2__0) 
                                     << (0x1fU & ((IData)(0x84U) 
                                                  + 
                                                  (0x1fffU 
                                                   & ((IData)(0x85U) 
                                                      * (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__enq_ptr)))))));
            }
            vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT____Vlvbound_h71839dcf__0 
                = vlSelfRef.hbm_controller_tb_simple__DOT__tb_req_id;
            if ((0x109fU >= ((IData)(0x64U) + (0x1fffU 
                                               & ((IData)(0x85U) 
                                                  * (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__enq_ptr)))))) {
                VL_ASSIGNSEL_WI(4256,32,((IData)(0x64U) 
                                         + (0x1fffU 
                                            & ((IData)(0x85U) 
                                               * (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__enq_ptr)))), vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue, vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT____Vlvbound_h71839dcf__0);
            }
            vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT____Vlvbound_h822848eb__0 
                = vlSelfRef.hbm_controller_tb_simple__DOT__tb_req_addr;
            if ((0x109fU >= ((IData)(0x40U) + (0x1fffU 
                                               & ((IData)(0x85U) 
                                                  * (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__enq_ptr)))))) {
                VL_ASSIGNSEL_WQ(4256,36,((IData)(0x40U) 
                                         + (0x1fffU 
                                            & ((IData)(0x85U) 
                                               * (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__enq_ptr)))), vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue, vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT____Vlvbound_h822848eb__0);
            }
            vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT____Vlvbound_h2ff16325__0 
                = vlSelfRef.hbm_controller_tb_simple__DOT__tb_req_rd_wr_n;
            if ((0x109fU >= ((IData)(0x3fU) + (0x1fffU 
                                               & ((IData)(0x85U) 
                                                  * (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__enq_ptr)))))) {
                vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[(
                                                                          ((IData)(0x3fU) 
                                                                           + 
                                                                           (0x1fffU 
                                                                            & ((IData)(0x85U) 
                                                                               * (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__enq_ptr)))) 
                                                                          >> 5U)] 
                    = (((~ ((IData)(1U) << (0x1fU & 
                                            ((IData)(0x3fU) 
                                             + (0x1fffU 
                                                & ((IData)(0x85U) 
                                                   * (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__enq_ptr))))))) 
                        & vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[
                        (((IData)(0x3fU) + (0x1fffU 
                                            & ((IData)(0x85U) 
                                               * (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__enq_ptr)))) 
                         >> 5U)]) | ((IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT____Vlvbound_h2ff16325__0) 
                                     << (0x1fU & ((IData)(0x3fU) 
                                                  + 
                                                  (0x1fffU 
                                                   & ((IData)(0x85U) 
                                                      * (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__enq_ptr)))))));
            }
            vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT____Vlvbound_h33e97cea__0 = 0x40U;
            if ((0x109fU >= ((IData)(0x2fU) + (0x1fffU 
                                               & ((IData)(0x85U) 
                                                  * (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__enq_ptr)))))) {
                VL_ASSIGNSEL_WI(4256,16,((IData)(0x2fU) 
                                         + (0x1fffU 
                                            & ((IData)(0x85U) 
                                               * (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__enq_ptr)))), vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue, vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT____Vlvbound_h33e97cea__0);
            }
            vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT____Vlvbound_h2e975fa7__0 = 0U;
            if ((0x109fU >= ((IData)(0x2cU) + (0x1fffU 
                                               & ((IData)(0x85U) 
                                                  * (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__enq_ptr)))))) {
                VL_ASSIGNSEL_WI(4256,3,((IData)(0x2cU) 
                                        + (0x1fffU 
                                           & ((IData)(0x85U) 
                                              * (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__enq_ptr)))), vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue, vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT____Vlvbound_h2e975fa7__0);
            }
            vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT____Vlvbound_h28b1ddf3__0 
                = vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__age_counter;
            if ((0x109fU >= ((IData)(4U) + (0x1fffU 
                                            & ((IData)(0x85U) 
                                               * (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__enq_ptr)))))) {
                VL_ASSIGNSEL_WI(4256,8,((IData)(4U) 
                                        + (0x1fffU 
                                           & ((IData)(0x85U) 
                                              * (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__enq_ptr)))), vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue, vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT____Vlvbound_h28b1ddf3__0);
            }
            vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT____Vlvbound_hb59a37e4__0 = 0U;
            if ((0x109fU >= (0x1fffU & ((IData)(0x85U) 
                                        * (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__enq_ptr))))) {
                VL_ASSIGNSEL_WI(4256,4,(0x1fffU & ((IData)(0x85U) 
                                                   * (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__enq_ptr))), vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue, vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT____Vlvbound_hb59a37e4__0);
            }
            vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT____Vlvbound_h26d43ea3__0 
                = (0x1fU & (IData)((vlSelfRef.hbm_controller_tb_simple__DOT__tb_req_addr 
                                    >> 0x1dU)));
            if ((0x109fU >= ((IData)(0x26U) + (0x1fffU 
                                               & ((IData)(0x85U) 
                                                  * (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__enq_ptr)))))) {
                VL_ASSIGNSEL_WI(4256,5,((IData)(0x26U) 
                                        + (0x1fffU 
                                           & ((IData)(0x85U) 
                                              * (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__enq_ptr)))), vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue, vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT____Vlvbound_h26d43ea3__0);
            }
            vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT____Vlvbound_h31965574__0 
                = (0xfU & (IData)((vlSelfRef.hbm_controller_tb_simple__DOT__tb_req_addr 
                                   >> 0x16U)));
            if ((0x109fU >= ((IData)(0x1fU) + (0x1fffU 
                                               & ((IData)(0x85U) 
                                                  * (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__enq_ptr)))))) {
                VL_ASSIGNSEL_WI(4256,4,((IData)(0x1fU) 
                                        + (0x1fffU 
                                           & ((IData)(0x85U) 
                                              * (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__enq_ptr)))), vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue, vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT____Vlvbound_h31965574__0);
            }
            vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT____Vlvbound_h2f30f8cf__0 
                = (0xffffU & (IData)((vlSelfRef.hbm_controller_tb_simple__DOT__tb_req_addr 
                                      >> 6U)));
            if ((0x109fU >= ((IData)(0xeU) + (0x1fffU 
                                              & ((IData)(0x85U) 
                                                 * (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__enq_ptr)))))) {
                VL_ASSIGNSEL_WI(4256,16,((IData)(0xeU) 
                                         + (0x1fffU 
                                            & ((IData)(0x85U) 
                                               * (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__enq_ptr)))), vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue, vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT____Vlvbound_h2f30f8cf__0);
            }
            vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT____Vlvbound_h2e8529d8__0 
                = (3U & (IData)((vlSelfRef.hbm_controller_tb_simple__DOT__tb_req_addr 
                                 >> 0x22U)));
            if ((0x109fU >= ((IData)(0xcU) + (0x1fffU 
                                              & ((IData)(0x85U) 
                                                 * (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__enq_ptr)))))) {
                VL_ASSIGNSEL_WI(4256,2,((IData)(0xcU) 
                                        + (0x1fffU 
                                           & ((IData)(0x85U) 
                                              * (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__enq_ptr)))), vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue, vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT____Vlvbound_h2e8529d8__0);
            }
            vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT____Vlvbound_h989f323f__0 
                = ((((0xfU & (IData)((vlSelfRef.hbm_controller_tb_simple__DOT__tb_req_addr 
                                      >> 0x16U))) == 
                     (0xfU & VL_SEL_IWII(128, vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_bank_reg, 
                                         (0x7fU & VL_SHIFTL_III(7,32,32, 
                                                                VL_EXTEND_II(32,5, 
                                                                             ([&]() {
                                                    __Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__0__ch 
                                                        = 
                                                        (0x1fU 
                                                         & (IData)(
                                                                   (vlSelfRef.hbm_controller_tb_simple__DOT__tb_req_addr 
                                                                    >> 0x1dU)));
                                                    __Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__0__Vfuncout 
                                                        = __Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__0__ch;
                                                }(), (IData)(__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__0__Vfuncout))), 2U)), 4U))) 
                    & ((0xffffU & (IData)((vlSelfRef.hbm_controller_tb_simple__DOT__tb_req_addr 
                                           >> 6U))) 
                       == (0xffffU & VL_SEL_IWII(512, vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_row_reg, 
                                                 (0x1ffU 
                                                  & VL_SHIFTL_III(9,32,32, 
                                                                  VL_EXTEND_II(32,5, 
                                                                               ([&]() {
                                                    __Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__1__ch 
                                                        = 
                                                        (0x1fU 
                                                         & (IData)(
                                                                   (vlSelfRef.hbm_controller_tb_simple__DOT__tb_req_addr 
                                                                    >> 0x1dU)));
                                                    __Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__1__Vfuncout 
                                                        = __Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__1__ch;
                                                }(), (IData)(__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__1__Vfuncout))), 4U)), 0x10U)))) 
                   & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__row_open 
                      >> ([&]() {
                            __Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__2__ch 
                                = (0x1fU & (IData)(
                                                   (vlSelfRef.hbm_controller_tb_simple__DOT__tb_req_addr 
                                                    >> 0x1dU)));
                            __Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__2__Vfuncout 
                                = __Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__2__ch;
                        }(), (IData)(__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__2__Vfuncout))));
            if ((0x109fU >= ((IData)(0x2bU) + (0x1fffU 
                                               & ((IData)(0x85U) 
                                                  * (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__enq_ptr)))))) {
                vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[(
                                                                          ((IData)(0x2bU) 
                                                                           + 
                                                                           (0x1fffU 
                                                                            & ((IData)(0x85U) 
                                                                               * (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__enq_ptr)))) 
                                                                          >> 5U)] 
                    = (((~ ((IData)(1U) << (0x1fU & 
                                            ((IData)(0x2bU) 
                                             + (0x1fffU 
                                                & ((IData)(0x85U) 
                                                   * (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__enq_ptr))))))) 
                        & vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[
                        (((IData)(0x2bU) + (0x1fffU 
                                            & ((IData)(0x85U) 
                                               * (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__enq_ptr)))) 
                         >> 5U)]) | ((IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT____Vlvbound_h989f323f__0) 
                                     << (0x1fU & ((IData)(0x2bU) 
                                                  + 
                                                  (0x1fffU 
                                                   & ((IData)(0x85U) 
                                                      * (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__enq_ptr)))))));
            }
        }
    } else {
        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[4U] 
            = (0xffffffefU & vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[4U]);
        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[8U] 
            = (0xfffffdffU & vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[8U]);
        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0xcU] 
            = (0xffffbfffU & vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0xcU]);
        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x10U] 
            = (0xfff7ffffU & vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x10U]);
        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x14U] 
            = (0xfeffffffU & vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x14U]);
        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x18U] 
            = (0xdfffffffU & vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x18U]);
        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x1dU] 
            = (0xfffffffbU & vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x1dU]);
        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x21U] 
            = (0xffffff7fU & vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x21U]);
        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x25U] 
            = (0xffffefffU & vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x25U]);
        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x29U] 
            = (0xfffdffffU & vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x29U]);
        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x2dU] 
            = (0xffbfffffU & vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x2dU]);
        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x31U] 
            = (0xf7ffffffU & vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x31U]);
        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x36U] 
            = (0xfffffffeU & vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x36U]);
        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x3aU] 
            = (0xffffffdfU & vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x3aU]);
        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x3eU] 
            = (0xfffffbffU & vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x3eU]);
        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x42U] 
            = (0xffff7fffU & vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x42U]);
        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x46U] 
            = (0xffefffffU & vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x46U]);
        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x4aU] 
            = (0xfdffffffU & vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x4aU]);
        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x4eU] 
            = (0xbfffffffU & vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x4eU]);
        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x53U] 
            = (0xfffffff7U & vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x53U]);
        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x57U] 
            = (0xfffffeffU & vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x57U]);
        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x5bU] 
            = (0xffffdfffU & vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x5bU]);
        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x5fU] 
            = (0xfffbffffU & vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x5fU]);
        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x63U] 
            = (0xff7fffffU & vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x63U]);
        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x67U] 
            = (0xefffffffU & vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x67U]);
        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x6cU] 
            = (0xfffffffdU & vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x6cU]);
        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x70U] 
            = (0xffffffbfU & vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x70U]);
        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x74U] 
            = (0xfffff7ffU & vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x74U]);
        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x78U] 
            = (0xfffeffffU & vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x78U]);
        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x7cU] 
            = (0xffdfffffU & vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x7cU]);
        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x80U] 
            = (0xfbffffffU & vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x80U]);
        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x84U] 
            = (0x7fffffffU & vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue[0x84U]);
    }
    vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__enq_ptr 
        = __Vdly__hbm_controller_tb_simple__DOT__dut__DOT__enq_ptr;
    vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__age_counter 
        = __Vdly__hbm_controller_tb_simple__DOT__dut__DOT__age_counter;
    if (vlSelfRef.hbm_controller_tb_simple__DOT__rst_n) {
        if (((IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__grant_valid) 
             & (0U == (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__state)))) {
            vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__grant_idx 
                = vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__best_idx;
        }
    } else {
        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__grant_idx = 0U;
    }
    if (vlSelfRef.hbm_controller_tb_simple__DOT__rst_n) {
        if ((1U == (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__tb_dram_cmd))) {
            __Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__3__ch 
                = (0x1fU & (IData)((vlSelfRef.hbm_controller_tb_simple__DOT__tb_req_addr 
                                    >> 0x1dU)));
            __Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__3__Vfuncout 
                = __Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__3__ch;
            __Vdly__hbm_controller_tb_simple__DOT__dut__DOT__open_pch_reg 
                = (((~ ((IData)(1U) << (IData)(__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__3__Vfuncout))) 
                    & __Vdly__hbm_controller_tb_simple__DOT__dut__DOT__open_pch_reg) 
                   | (0xffffffffULL & ((1U & (IData)(
                                                     (vlSelfRef.hbm_controller_tb_simple__DOT__tb_req_addr 
                                                      >> 0x1dU))) 
                                       << (IData)(__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__3__Vfuncout))));
            vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT____Vlvbound_h7936eb07__0 
                = (7U & (IData)((vlSelfRef.hbm_controller_tb_simple__DOT__tb_req_addr 
                                 >> 0x1aU)));
            if (VL_LIKELY(((0x5fU >= (0x7fU & ((IData)(3U) 
                                               * VL_EXTEND_II(32,5, 
                                                              ([&]() {
                                                __Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__4__ch 
                                                    = 
                                                    (0x1fU 
                                                     & (IData)(
                                                               (vlSelfRef.hbm_controller_tb_simple__DOT__tb_req_addr 
                                                                >> 0x1dU)));
                                                __Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__4__Vfuncout 
                                                    = __Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__4__ch;
                                            }(), (IData)(__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__4__Vfuncout))))))))) {
                __Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__5__ch 
                    = (0x1fU & (IData)((vlSelfRef.hbm_controller_tb_simple__DOT__tb_req_addr 
                                        >> 0x1dU)));
                __Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__5__Vfuncout 
                    = __Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__5__ch;
                VL_ASSIGNSEL_WI(96,3,(0x7fU & ((IData)(3U) 
                                               * (IData)(__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__5__Vfuncout))), __Vdly__hbm_controller_tb_simple__DOT__dut__DOT__open_bg_reg, vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT____Vlvbound_h7936eb07__0);
            }
            __Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__6__ch 
                = (0x1fU & (IData)((vlSelfRef.hbm_controller_tb_simple__DOT__tb_req_addr 
                                    >> 0x1dU)));
            __Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__6__Vfuncout 
                = __Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__6__ch;
            VL_ASSIGNSEL_WI(128,4,(0x7fU & VL_SHIFTL_III(7,32,32, (IData)(__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__6__Vfuncout), 2U)), __Vdly__hbm_controller_tb_simple__DOT__dut__DOT__open_bank_reg, 
                            (0xfU & (IData)((vlSelfRef.hbm_controller_tb_simple__DOT__tb_req_addr 
                                             >> 0x16U))));
            __Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__7__ch 
                = (0x1fU & (IData)((vlSelfRef.hbm_controller_tb_simple__DOT__tb_req_addr 
                                    >> 0x1dU)));
            __Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__7__Vfuncout 
                = __Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__7__ch;
            VL_ASSIGNSEL_WI(512,16,(0x1ffU & VL_SHIFTL_III(9,32,32, (IData)(__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__7__Vfuncout), 4U)), vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_row_reg, 
                            (0xffffU & (IData)((vlSelfRef.hbm_controller_tb_simple__DOT__tb_req_addr 
                                                >> 6U))));
            __Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__8__ch 
                = (0x1fU & (IData)((vlSelfRef.hbm_controller_tb_simple__DOT__tb_req_addr 
                                    >> 0x1dU)));
            __Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__8__Vfuncout 
                = __Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__8__ch;
            vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__row_open 
                = (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__row_open 
                   | (0xffffffffULL & ((IData)(1U) 
                                       << (IData)(__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__8__Vfuncout))));
        } else if ((4U == (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__tb_dram_cmd))) {
            if (((((1U & (IData)((vlSelfRef.hbm_controller_tb_simple__DOT__tb_req_addr 
                                  >> 0x1dU))) == (1U 
                                                  & (vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_pch_reg 
                                                     >> 
                                                     ([&]() {
                                            __Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__9__ch 
                                                = (0x1fU 
                                                   & (IData)(
                                                             (vlSelfRef.hbm_controller_tb_simple__DOT__tb_req_addr 
                                                              >> 0x1dU)));
                                            __Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__9__Vfuncout 
                                                = __Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__9__ch;
                                        }(), (IData)(__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__9__Vfuncout))))) 
                  & ((7U & (IData)((vlSelfRef.hbm_controller_tb_simple__DOT__tb_req_addr 
                                    >> 0x1aU))) == 
                     ((0x5fU >= (0x7fU & ((IData)(3U) 
                                          * VL_EXTEND_II(32,5, 
                                                         ([&]() {
                                                        __Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__10__ch 
                                                            = 
                                                            (0x1fU 
                                                             & (IData)(
                                                                       (vlSelfRef.hbm_controller_tb_simple__DOT__tb_req_addr 
                                                                        >> 0x1dU)));
                                                        __Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__10__Vfuncout 
                                                            = __Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__10__ch;
                                                    }(), (IData)(__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__10__Vfuncout))))))
                       ? (7U & VL_SEL_IWII(96, vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_bg_reg, 
                                           (0x7fU & 
                                            ((IData)(3U) 
                                             * VL_EXTEND_II(32,5, 
                                                            ([&]() {
                                                            __Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__11__ch 
                                                                = 
                                                                (0x1fU 
                                                                 & (IData)(
                                                                           (vlSelfRef.hbm_controller_tb_simple__DOT__tb_req_addr 
                                                                            >> 0x1dU)));
                                                            __Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__11__Vfuncout 
                                                                = __Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__11__ch;
                                                        }(), (IData)(__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__11__Vfuncout))))), 3U))
                       : 0U))) & ((0xfU & (IData)((vlSelfRef.hbm_controller_tb_simple__DOT__tb_req_addr 
                                                   >> 0x16U))) 
                                  == (0xfU & VL_SEL_IWII(128, vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_bank_reg, 
                                                         (0x7fU 
                                                          & VL_SHIFTL_III(7,32,32, 
                                                                          VL_EXTEND_II(32,5, 
                                                                                ([&]() {
                                                    __Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__12__ch 
                                                        = 
                                                        (0x1fU 
                                                         & (IData)(
                                                                   (vlSelfRef.hbm_controller_tb_simple__DOT__tb_req_addr 
                                                                    >> 0x1dU)));
                                                    __Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__12__Vfuncout 
                                                        = __Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__12__ch;
                                                }(), (IData)(__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__12__Vfuncout))), 2U)), 4U))))) {
                __Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__13__ch 
                    = (0x1fU & (IData)((vlSelfRef.hbm_controller_tb_simple__DOT__tb_req_addr 
                                        >> 0x1dU)));
                __Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__13__Vfuncout 
                    = __Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__13__ch;
                vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__row_open 
                    = ((~ ((IData)(1U) << (IData)(__Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__13__Vfuncout))) 
                       & vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__row_open);
            }
        }
    } else {
        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__row_open = 0U;
        __Vdly__hbm_controller_tb_simple__DOT__dut__DOT__open_pch_reg = 0U;
        __Vdly__hbm_controller_tb_simple__DOT__dut__DOT__open_bg_reg[0U] = 0U;
        __Vdly__hbm_controller_tb_simple__DOT__dut__DOT__open_bg_reg[1U] = 0U;
        __Vdly__hbm_controller_tb_simple__DOT__dut__DOT__open_bg_reg[2U] = 0U;
        __Vdly__hbm_controller_tb_simple__DOT__dut__DOT__open_bank_reg[0U] = 0U;
        __Vdly__hbm_controller_tb_simple__DOT__dut__DOT__open_bank_reg[1U] = 0U;
        __Vdly__hbm_controller_tb_simple__DOT__dut__DOT__open_bank_reg[2U] = 0U;
        __Vdly__hbm_controller_tb_simple__DOT__dut__DOT__open_bank_reg[3U] = 0U;
        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_row_reg[0U] 
            = Vhbm_controller_tb_simple__ConstPool__CONST_h93e1b771_0[0U];
        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_row_reg[1U] 
            = Vhbm_controller_tb_simple__ConstPool__CONST_h93e1b771_0[1U];
        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_row_reg[2U] 
            = Vhbm_controller_tb_simple__ConstPool__CONST_h93e1b771_0[2U];
        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_row_reg[3U] 
            = Vhbm_controller_tb_simple__ConstPool__CONST_h93e1b771_0[3U];
        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_row_reg[4U] 
            = Vhbm_controller_tb_simple__ConstPool__CONST_h93e1b771_0[4U];
        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_row_reg[5U] 
            = Vhbm_controller_tb_simple__ConstPool__CONST_h93e1b771_0[5U];
        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_row_reg[6U] 
            = Vhbm_controller_tb_simple__ConstPool__CONST_h93e1b771_0[6U];
        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_row_reg[7U] 
            = Vhbm_controller_tb_simple__ConstPool__CONST_h93e1b771_0[7U];
        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_row_reg[8U] 
            = Vhbm_controller_tb_simple__ConstPool__CONST_h93e1b771_0[8U];
        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_row_reg[9U] 
            = Vhbm_controller_tb_simple__ConstPool__CONST_h93e1b771_0[9U];
        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_row_reg[0xaU] 
            = Vhbm_controller_tb_simple__ConstPool__CONST_h93e1b771_0[0xaU];
        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_row_reg[0xbU] 
            = Vhbm_controller_tb_simple__ConstPool__CONST_h93e1b771_0[0xbU];
        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_row_reg[0xcU] 
            = Vhbm_controller_tb_simple__ConstPool__CONST_h93e1b771_0[0xcU];
        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_row_reg[0xdU] 
            = Vhbm_controller_tb_simple__ConstPool__CONST_h93e1b771_0[0xdU];
        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_row_reg[0xeU] 
            = Vhbm_controller_tb_simple__ConstPool__CONST_h93e1b771_0[0xeU];
        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_row_reg[0xfU] 
            = Vhbm_controller_tb_simple__ConstPool__CONST_h93e1b771_0[0xfU];
    }
    if (vlSelfRef.hbm_controller_tb_simple__DOT__rst_n) {
        vlSelfRef.hbm_controller_tb_simple__DOT__tb_dram_cmd = 0U;
        if ((1U == (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__state))) {
            vlSelfRef.hbm_controller_tb_simple__DOT__tb_dram_cmd = 1U;
        } else if ((2U == (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__state))) {
            vlSelfRef.hbm_controller_tb_simple__DOT__tb_dram_cmd = 2U;
        } else if ((3U == (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__state))) {
            vlSelfRef.hbm_controller_tb_simple__DOT__tb_dram_cmd = 3U;
        } else if ((4U == (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__state))) {
            vlSelfRef.hbm_controller_tb_simple__DOT__tb_dram_cmd = 4U;
        }
    } else {
        vlSelfRef.hbm_controller_tb_simple__DOT__tb_dram_cmd = 0U;
    }
    vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_pch_reg 
        = __Vdly__hbm_controller_tb_simple__DOT__dut__DOT__open_pch_reg;
    vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_bg_reg[0U] 
        = __Vdly__hbm_controller_tb_simple__DOT__dut__DOT__open_bg_reg[0U];
    vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_bg_reg[1U] 
        = __Vdly__hbm_controller_tb_simple__DOT__dut__DOT__open_bg_reg[1U];
    vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_bg_reg[2U] 
        = __Vdly__hbm_controller_tb_simple__DOT__dut__DOT__open_bg_reg[2U];
    vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_bank_reg[0U] 
        = __Vdly__hbm_controller_tb_simple__DOT__dut__DOT__open_bank_reg[0U];
    vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_bank_reg[1U] 
        = __Vdly__hbm_controller_tb_simple__DOT__dut__DOT__open_bank_reg[1U];
    vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_bank_reg[2U] 
        = __Vdly__hbm_controller_tb_simple__DOT__dut__DOT__open_bank_reg[2U];
    vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__open_bank_reg[3U] 
        = __Vdly__hbm_controller_tb_simple__DOT__dut__DOT__open_bank_reg[3U];
}

VL_INLINE_OPT void Vhbm_controller_tb_simple___024root___nba_sequent__TOP__1(Vhbm_controller_tb_simple___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vhbm_controller_tb_simple___024root___nba_sequent__TOP__1\n"); );
    Vhbm_controller_tb_simple__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Init
    IData/*31:0*/ __Vdly__hbm_controller_tb_simple__DOT__cycle;
    __Vdly__hbm_controller_tb_simple__DOT__cycle = 0;
    IData/*31:0*/ __Vdly__hbm_controller_tb_simple__DOT__resp_count;
    __Vdly__hbm_controller_tb_simple__DOT__resp_count = 0;
    // Body
    __Vdly__hbm_controller_tb_simple__DOT__cycle = vlSelfRef.hbm_controller_tb_simple__DOT__cycle;
    vlSelfRef.__Vdly__hbm_controller_tb_simple__DOT__tb_req_valid 
        = vlSelfRef.hbm_controller_tb_simple__DOT__tb_req_valid;
    __Vdly__hbm_controller_tb_simple__DOT__resp_count 
        = vlSelfRef.hbm_controller_tb_simple__DOT__resp_count;
    vlSelfRef.__Vdly__hbm_controller_tb_simple__DOT__rst_n 
        = vlSelfRef.hbm_controller_tb_simple__DOT__rst_n;
    if (vlSelfRef.hbm_controller_tb_simple__DOT__rst_n) {
        __Vdly__hbm_controller_tb_simple__DOT__cycle 
            = ((IData)(1U) + vlSelfRef.hbm_controller_tb_simple__DOT__cycle);
        if (VL_UNLIKELY(((1U == vlSelfRef.hbm_controller_tb_simple__DOT__cycle)))) {
            VL_WRITEF_NX("Test 1: Read request at cycle %11d\n",0,
                         32,vlSelfRef.hbm_controller_tb_simple__DOT__cycle);
            vlSelfRef.__Vdly__hbm_controller_tb_simple__DOT__tb_req_valid = 1U;
            vlSelfRef.hbm_controller_tb_simple__DOT__tb_req_id = 1U;
            vlSelfRef.hbm_controller_tb_simple__DOT__tb_req_addr = 0x10000ULL;
            vlSelfRef.hbm_controller_tb_simple__DOT__tb_req_rd_wr_n = 1U;
        }
        if (VL_UNLIKELY((((2U == vlSelfRef.hbm_controller_tb_simple__DOT__cycle) 
                          & (0x20U > (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue_count)))))) {
            VL_WRITEF_NX("Request accepted at cycle %11d\n",0,
                         32,vlSelfRef.hbm_controller_tb_simple__DOT__cycle);
            vlSelfRef.__Vdly__hbm_controller_tb_simple__DOT__tb_req_valid = 0U;
        }
        if (VL_UNLIKELY((vlSelfRef.hbm_controller_tb_simple__DOT__tb_resp_valid))) {
            VL_WRITEF_NX("Response: id=%x success=%b status=%x at cycle %11d\n",0,
                         32,vlSelfRef.hbm_controller_tb_simple__DOT__tb_resp_id,
                         1,(IData)(vlSelfRef.hbm_controller_tb_simple__DOT__tb_resp_success),
                         8,vlSelfRef.hbm_controller_tb_simple__DOT__tb_resp_status,
                         32,vlSelfRef.hbm_controller_tb_simple__DOT__cycle);
            __Vdly__hbm_controller_tb_simple__DOT__resp_count 
                = ((IData)(1U) + vlSelfRef.hbm_controller_tb_simple__DOT__resp_count);
        }
        if (VL_UNLIKELY(((0x14U == vlSelfRef.hbm_controller_tb_simple__DOT__cycle)))) {
            VL_WRITEF_NX("Test 2: Write request at cycle %11d\n",0,
                         32,vlSelfRef.hbm_controller_tb_simple__DOT__cycle);
            vlSelfRef.__Vdly__hbm_controller_tb_simple__DOT__tb_req_valid = 1U;
            vlSelfRef.hbm_controller_tb_simple__DOT__tb_req_id = 2U;
            vlSelfRef.hbm_controller_tb_simple__DOT__tb_req_addr = 0x20000ULL;
            vlSelfRef.hbm_controller_tb_simple__DOT__tb_req_rd_wr_n = 0U;
        }
        if (VL_UNLIKELY((((0x15U == vlSelfRef.hbm_controller_tb_simple__DOT__cycle) 
                          & (0x20U > (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue_count)))))) {
            VL_WRITEF_NX("Write accepted at cycle %11d\n",0,
                         32,vlSelfRef.hbm_controller_tb_simple__DOT__cycle);
            vlSelfRef.__Vdly__hbm_controller_tb_simple__DOT__tb_req_valid = 0U;
        }
        if (VL_UNLIKELY(((0x32U == vlSelfRef.hbm_controller_tb_simple__DOT__cycle)))) {
            VL_WRITEF_NX("========================================\nTest Complete at cycle %11d\nResponses received: %11d\nStats: req=%10# completed=%10# hit_rate=%3#%%\n========================================\n",0,
                         32,vlSelfRef.hbm_controller_tb_simple__DOT__cycle,
                         32,vlSelfRef.hbm_controller_tb_simple__DOT__resp_count,
                         32,vlSelfRef.hbm_controller_tb_simple__DOT__tb_stat_requests,
                         32,vlSelfRef.hbm_controller_tb_simple__DOT__tb_stat_completed,
                         8,(IData)(vlSelfRef.hbm_controller_tb_simple__DOT__tb_stat_hit_rate));
            VL_FINISH_MT("/home/ic/JXTF/HBM/rtl/hbm_controller_tb_simple.sv", 138, "");
        }
    } else {
        __Vdly__hbm_controller_tb_simple__DOT__cycle 
            = ((IData)(1U) + vlSelfRef.hbm_controller_tb_simple__DOT__cycle);
        if (VL_UNLIKELY(((5U == vlSelfRef.hbm_controller_tb_simple__DOT__cycle)))) {
            VL_WRITEF_NX("Reset released at cycle 0\n",0);
            vlSelfRef.__Vdly__hbm_controller_tb_simple__DOT__rst_n = 1U;
            __Vdly__hbm_controller_tb_simple__DOT__cycle = 0U;
        }
    }
    vlSelfRef.hbm_controller_tb_simple__DOT__cycle 
        = __Vdly__hbm_controller_tb_simple__DOT__cycle;
    vlSelfRef.hbm_controller_tb_simple__DOT__resp_count 
        = __Vdly__hbm_controller_tb_simple__DOT__resp_count;
}

extern const VlUnpacked<CData/*3:0*/, 256> Vhbm_controller_tb_simple__ConstPool__TABLE_hea14f260_0;

VL_INLINE_OPT void Vhbm_controller_tb_simple___024root___nba_sequent__TOP__2(Vhbm_controller_tb_simple___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vhbm_controller_tb_simple___024root___nba_sequent__TOP__2\n"); );
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
    if (vlSelfRef.hbm_controller_tb_simple__DOT__rst_n) {
        if (((IData)(vlSelfRef.hbm_controller_tb_simple__DOT__tb_req_valid) 
             & (0x20U > (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue_count)))) {
            vlSelfRef.__Vdly__hbm_controller_tb_simple__DOT__dut__DOT__requests_q 
                = ((IData)(1U) + vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__requests_q);
        }
        if (vlSelfRef.hbm_controller_tb_simple__DOT__tb_resp_valid) {
            vlSelfRef.__Vdly__hbm_controller_tb_simple__DOT__dut__DOT__completed_q 
                = ((IData)(1U) + vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__completed_q);
        }
        vlSelfRef.hbm_controller_tb_simple__DOT__tb_stat_requests 
            = vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__requests_q;
        vlSelfRef.hbm_controller_tb_simple__DOT__tb_stat_completed 
            = vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__completed_q;
        vlSelfRef.hbm_controller_tb_simple__DOT__tb_stat_hit_rate 
            = ((0U < vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__requests_q)
                ? (0xffU & VL_DIV_III(32, ((IData)(0x64U) 
                                           * vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__completed_q), vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__requests_q))
                : 0U);
        vlSelfRef.hbm_controller_tb_simple__DOT__tb_resp_valid = 0U;
        vlSelfRef.__Vdly__hbm_controller_tb_simple__DOT__dut__DOT__resp_issued = 0U;
        if (((5U == (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__state)) 
             & (~ (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__resp_issued)))) {
            vlSelfRef.hbm_controller_tb_simple__DOT__tb_resp_valid = 1U;
            vlSelfRef.hbm_controller_tb_simple__DOT__tb_resp_id 
                = vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__cur_id;
            vlSelfRef.hbm_controller_tb_simple__DOT__tb_resp_success = 1U;
            vlSelfRef.hbm_controller_tb_simple__DOT__tb_resp_status = 0U;
            vlSelfRef.__Vdly__hbm_controller_tb_simple__DOT__dut__DOT__resp_issued = 1U;
        }
        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__state 
            = vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__next_state;
    } else {
        vlSelfRef.__Vdly__hbm_controller_tb_simple__DOT__dut__DOT__requests_q = 0U;
        vlSelfRef.__Vdly__hbm_controller_tb_simple__DOT__dut__DOT__completed_q = 0U;
        vlSelfRef.__Vdly__hbm_controller_tb_simple__DOT__dut__DOT__resp_issued = 0U;
        vlSelfRef.hbm_controller_tb_simple__DOT__tb_resp_valid = 0U;
        vlSelfRef.hbm_controller_tb_simple__DOT__tb_resp_id = 0U;
        vlSelfRef.hbm_controller_tb_simple__DOT__tb_resp_success = 0U;
        vlSelfRef.hbm_controller_tb_simple__DOT__tb_resp_status = 0U;
        vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__state = 0U;
    }
    vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__requests_q 
        = vlSelfRef.__Vdly__hbm_controller_tb_simple__DOT__dut__DOT__requests_q;
    vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__completed_q 
        = vlSelfRef.__Vdly__hbm_controller_tb_simple__DOT__dut__DOT__completed_q;
    vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue_count 
        = vlSelfRef.__Vdly__hbm_controller_tb_simple__DOT__dut__DOT__queue_count;
    vlSelfRef.hbm_controller_tb_simple__DOT__tb_req_ready 
        = (0x20U > (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue_count));
    vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue_empty 
        = (0U == (IData)(vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__queue_count));
    vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__cur_id 
        = vlSelfRef.__Vdly__hbm_controller_tb_simple__DOT__dut__DOT__cur_id;
    vlSelfRef.hbm_controller_tb_simple__DOT__dut__DOT__resp_issued 
        = vlSelfRef.__Vdly__hbm_controller_tb_simple__DOT__dut__DOT__resp_issued;
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

VL_INLINE_OPT void Vhbm_controller_tb_simple___024root___nba_sequent__TOP__3(Vhbm_controller_tb_simple___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vhbm_controller_tb_simple___024root___nba_sequent__TOP__3\n"); );
    Vhbm_controller_tb_simple__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    vlSelfRef.hbm_controller_tb_simple__DOT__tb_req_valid 
        = vlSelfRef.__Vdly__hbm_controller_tb_simple__DOT__tb_req_valid;
    vlSelfRef.hbm_controller_tb_simple__DOT__rst_n 
        = vlSelfRef.__Vdly__hbm_controller_tb_simple__DOT__rst_n;
}

void Vhbm_controller_tb_simple___024root___eval_triggers__act(Vhbm_controller_tb_simple___024root* vlSelf);

bool Vhbm_controller_tb_simple___024root___eval_phase__act(Vhbm_controller_tb_simple___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vhbm_controller_tb_simple___024root___eval_phase__act\n"); );
    Vhbm_controller_tb_simple__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Init
    VlTriggerVec<2> __VpreTriggered;
    CData/*0:0*/ __VactExecute;
    // Body
    Vhbm_controller_tb_simple___024root___eval_triggers__act(vlSelf);
    __VactExecute = vlSelfRef.__VactTriggered.any();
    if (__VactExecute) {
        __VpreTriggered.andNot(vlSelfRef.__VactTriggered, vlSelfRef.__VnbaTriggered);
        vlSelfRef.__VnbaTriggered.thisOr(vlSelfRef.__VactTriggered);
        Vhbm_controller_tb_simple___024root___eval_act(vlSelf);
    }
    return (__VactExecute);
}

bool Vhbm_controller_tb_simple___024root___eval_phase__nba(Vhbm_controller_tb_simple___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vhbm_controller_tb_simple___024root___eval_phase__nba\n"); );
    Vhbm_controller_tb_simple__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Init
    CData/*0:0*/ __VnbaExecute;
    // Body
    __VnbaExecute = vlSelfRef.__VnbaTriggered.any();
    if (__VnbaExecute) {
        Vhbm_controller_tb_simple___024root___eval_nba(vlSelf);
        vlSelfRef.__VnbaTriggered.clear();
    }
    return (__VnbaExecute);
}

#ifdef VL_DEBUG
VL_ATTR_COLD void Vhbm_controller_tb_simple___024root___dump_triggers__nba(Vhbm_controller_tb_simple___024root* vlSelf);
#endif  // VL_DEBUG
#ifdef VL_DEBUG
VL_ATTR_COLD void Vhbm_controller_tb_simple___024root___dump_triggers__act(Vhbm_controller_tb_simple___024root* vlSelf);
#endif  // VL_DEBUG

void Vhbm_controller_tb_simple___024root___eval(Vhbm_controller_tb_simple___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vhbm_controller_tb_simple___024root___eval\n"); );
    Vhbm_controller_tb_simple__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Init
    IData/*31:0*/ __VnbaIterCount;
    CData/*0:0*/ __VnbaContinue;
    // Body
    __VnbaIterCount = 0U;
    __VnbaContinue = 1U;
    while (__VnbaContinue) {
        if (VL_UNLIKELY(((0x64U < __VnbaIterCount)))) {
#ifdef VL_DEBUG
            Vhbm_controller_tb_simple___024root___dump_triggers__nba(vlSelf);
#endif
            VL_FATAL_MT("/home/ic/JXTF/HBM/rtl/hbm_controller_tb_simple.sv", 9, "", "NBA region did not converge.");
        }
        __VnbaIterCount = ((IData)(1U) + __VnbaIterCount);
        __VnbaContinue = 0U;
        vlSelfRef.__VactIterCount = 0U;
        vlSelfRef.__VactContinue = 1U;
        while (vlSelfRef.__VactContinue) {
            if (VL_UNLIKELY(((0x64U < vlSelfRef.__VactIterCount)))) {
#ifdef VL_DEBUG
                Vhbm_controller_tb_simple___024root___dump_triggers__act(vlSelf);
#endif
                VL_FATAL_MT("/home/ic/JXTF/HBM/rtl/hbm_controller_tb_simple.sv", 9, "", "Active region did not converge.");
            }
            vlSelfRef.__VactIterCount = ((IData)(1U) 
                                         + vlSelfRef.__VactIterCount);
            vlSelfRef.__VactContinue = 0U;
            if (Vhbm_controller_tb_simple___024root___eval_phase__act(vlSelf)) {
                vlSelfRef.__VactContinue = 1U;
            }
        }
        if (Vhbm_controller_tb_simple___024root___eval_phase__nba(vlSelf)) {
            __VnbaContinue = 1U;
        }
    }
}

#ifdef VL_DEBUG
void Vhbm_controller_tb_simple___024root___eval_debug_assertions(Vhbm_controller_tb_simple___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vhbm_controller_tb_simple___024root___eval_debug_assertions\n"); );
    Vhbm_controller_tb_simple__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    if (VL_UNLIKELY(((vlSelfRef.clk & 0xfeU)))) {
        Verilated::overWidthError("clk");}
}
#endif  // VL_DEBUG
