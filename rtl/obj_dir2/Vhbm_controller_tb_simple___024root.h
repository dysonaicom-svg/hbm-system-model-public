// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design internal header
// See Vhbm_controller_tb_simple.h for the primary calling header

#ifndef VERILATED_VHBM_CONTROLLER_TB_SIMPLE___024ROOT_H_
#define VERILATED_VHBM_CONTROLLER_TB_SIMPLE___024ROOT_H_  // guard

#include "verilated.h"


class Vhbm_controller_tb_simple__Syms;

class alignas(VL_CACHE_LINE_BYTES) Vhbm_controller_tb_simple___024root final : public VerilatedModule {
  public:

    // DESIGN SPECIFIC STATE
    // Anonymous structures to workaround compiler member-count bugs
    struct {
        CData/*0:0*/ hbm_controller_tb_simple__DOT__clk;
        CData/*0:0*/ hbm_controller_tb_simple__DOT__rst_n;
        CData/*0:0*/ hbm_controller_tb_simple__DOT__tb_req_valid;
        CData/*0:0*/ hbm_controller_tb_simple__DOT__tb_req_rd_wr_n;
        CData/*0:0*/ hbm_controller_tb_simple__DOT__tb_req_ready;
        CData/*0:0*/ hbm_controller_tb_simple__DOT__tb_resp_valid;
        CData/*0:0*/ hbm_controller_tb_simple__DOT__tb_resp_success;
        CData/*7:0*/ hbm_controller_tb_simple__DOT__tb_resp_status;
        CData/*3:0*/ hbm_controller_tb_simple__DOT__tb_dram_cmd;
        CData/*7:0*/ hbm_controller_tb_simple__DOT__tb_stat_hit_rate;
        CData/*4:0*/ hbm_controller_tb_simple__DOT__dut__DOT__enq_ptr;
        CData/*5:0*/ hbm_controller_tb_simple__DOT__dut__DOT__queue_count;
        CData/*7:0*/ hbm_controller_tb_simple__DOT__dut__DOT__age_counter;
        CData/*0:0*/ hbm_controller_tb_simple__DOT__dut__DOT__queue_empty;
        IData/*31:0*/ hbm_controller_tb_simple__DOT__dut__DOT__open_pch_reg;
        VlWide<3>/*95:0*/ hbm_controller_tb_simple__DOT__dut__DOT__open_bg_reg;
        VlWide<4>/*127:0*/ hbm_controller_tb_simple__DOT__dut__DOT__open_bank_reg;
        CData/*4:0*/ hbm_controller_tb_simple__DOT__dut__DOT__best_idx;
        CData/*0:0*/ hbm_controller_tb_simple__DOT__dut__DOT__best_row_hit;
        CData/*0:0*/ hbm_controller_tb_simple__DOT__dut__DOT__grant_valid;
        CData/*4:0*/ hbm_controller_tb_simple__DOT__dut__DOT__grant_idx;
        CData/*0:0*/ hbm_controller_tb_simple__DOT__dut__DOT__grant_row_hit;
        CData/*0:0*/ hbm_controller_tb_simple__DOT__dut__DOT__grant_rd_wr_n;
        CData/*3:0*/ hbm_controller_tb_simple__DOT__dut__DOT__state;
        CData/*3:0*/ hbm_controller_tb_simple__DOT__dut__DOT__next_state;
        CData/*0:0*/ hbm_controller_tb_simple__DOT__dut__DOT__txn_started;
        CData/*0:0*/ hbm_controller_tb_simple__DOT__dut__DOT__resp_issued;
        CData/*0:0*/ hbm_controller_tb_simple__DOT__dut__DOT____Vlvbound_h99c89ea2__0;
        CData/*0:0*/ hbm_controller_tb_simple__DOT__dut__DOT____Vlvbound_h2ff16325__0;
        CData/*2:0*/ hbm_controller_tb_simple__DOT__dut__DOT____Vlvbound_h2e975fa7__0;
        CData/*7:0*/ hbm_controller_tb_simple__DOT__dut__DOT____Vlvbound_h28b1ddf3__0;
        CData/*3:0*/ hbm_controller_tb_simple__DOT__dut__DOT____Vlvbound_hb59a37e4__0;
        CData/*4:0*/ hbm_controller_tb_simple__DOT__dut__DOT____Vlvbound_h26d43ea3__0;
        CData/*3:0*/ hbm_controller_tb_simple__DOT__dut__DOT____Vlvbound_h31965574__0;
        CData/*1:0*/ hbm_controller_tb_simple__DOT__dut__DOT____Vlvbound_h2e8529d8__0;
        CData/*0:0*/ hbm_controller_tb_simple__DOT__dut__DOT____Vlvbound_h989f323f__0;
        CData/*2:0*/ hbm_controller_tb_simple__DOT__dut__DOT____Vlvbound_h7936eb07__0;
        CData/*0:0*/ hbm_controller_tb_simple__DOT__dut__DOT____Vlvbound_hb8feabb2__0;
        CData/*0:0*/ __Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__Vfuncout;
        CData/*4:0*/ __Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_ch;
        CData/*0:0*/ __Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_pch;
        CData/*2:0*/ __Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bg;
        CData/*3:0*/ __Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_bank;
        CData/*4:0*/ __Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__Vfuncout;
        CData/*4:0*/ __Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__15__ch;
        CData/*4:0*/ __Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__Vfuncout;
        CData/*4:0*/ __Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__16__ch;
        CData/*4:0*/ __Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__Vfuncout;
        CData/*4:0*/ __Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__17__ch;
        CData/*4:0*/ __Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__Vfuncout;
        CData/*4:0*/ __Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__18__ch;
        CData/*4:0*/ __Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__Vfuncout;
        CData/*4:0*/ __Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__19__ch;
        CData/*4:0*/ __Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__Vfuncout;
        CData/*4:0*/ __Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__get_ch_idx__20__ch;
        CData/*0:0*/ __Vdly__hbm_controller_tb_simple__DOT__tb_req_valid;
        CData/*0:0*/ __Vdly__hbm_controller_tb_simple__DOT__rst_n;
        CData/*5:0*/ __Vdly__hbm_controller_tb_simple__DOT__dut__DOT__queue_count;
        CData/*0:0*/ __Vdly__hbm_controller_tb_simple__DOT__dut__DOT__resp_issued;
        CData/*0:0*/ __Vtrigprevexpr___TOP__hbm_controller_tb_simple__DOT__clk__0;
        CData/*0:0*/ __VstlDidInit;
        CData/*0:0*/ __VstlFirstIteration;
        CData/*0:0*/ __Vtrigprevexpr___TOP__hbm_controller_tb_simple__DOT__clk__1;
        CData/*0:0*/ __Vtrigprevexpr___TOP__hbm_controller_tb_simple__DOT__rst_n__0;
    };
    struct {
        CData/*0:0*/ __VactDidInit;
        CData/*0:0*/ __VactContinue;
        VlWide<16>/*511:0*/ hbm_controller_tb_simple__DOT__dut__DOT__open_row_reg;
        SData/*15:0*/ hbm_controller_tb_simple__DOT__dut__DOT____Vlvbound_h33e97cea__0;
        SData/*15:0*/ hbm_controller_tb_simple__DOT__dut__DOT____Vlvbound_h2f30f8cf__0;
        SData/*15:0*/ __Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__q_row;
        IData/*31:0*/ hbm_controller_tb_simple__DOT__tb_req_id;
        IData/*31:0*/ hbm_controller_tb_simple__DOT__tb_resp_id;
        IData/*31:0*/ hbm_controller_tb_simple__DOT__tb_stat_requests;
        IData/*31:0*/ hbm_controller_tb_simple__DOT__tb_stat_completed;
        IData/*31:0*/ hbm_controller_tb_simple__DOT__cycle;
        IData/*31:0*/ hbm_controller_tb_simple__DOT__resp_count;
        IData/*31:0*/ hbm_controller_tb_simple__DOT__dut__DOT__row_open;
        IData/*31:0*/ hbm_controller_tb_simple__DOT__dut__DOT__cur_id;
        IData/*31:0*/ hbm_controller_tb_simple__DOT__dut__DOT__requests_q;
        IData/*31:0*/ hbm_controller_tb_simple__DOT__dut__DOT__completed_q;
        IData/*31:0*/ hbm_controller_tb_simple__DOT__dut__DOT____Vlvbound_h71839dcf__0;
        IData/*31:0*/ __Vdly__hbm_controller_tb_simple__DOT__dut__DOT__cur_id;
        IData/*31:0*/ __Vdly__hbm_controller_tb_simple__DOT__dut__DOT__requests_q;
        IData/*31:0*/ __Vdly__hbm_controller_tb_simple__DOT__dut__DOT__completed_q;
        IData/*31:0*/ __VactIterCount;
        QData/*35:0*/ hbm_controller_tb_simple__DOT__tb_req_addr;
        VlWide<133>/*4255:0*/ hbm_controller_tb_simple__DOT__dut__DOT__queue;
        QData/*35:0*/ hbm_controller_tb_simple__DOT__dut__DOT____Vlvbound_h822848eb__0;
        QData/*35:0*/ __Vfunc_hbm_controller_tb_simple__DOT__dut__DOT__check_row_hit__14__addr;
    };
    VlTriggerVec<2> __VstlTriggered;
    VlTriggerVec<3> __VactTriggered;
    VlTriggerVec<3> __VnbaTriggered;

    // INTERNAL VARIABLES
    Vhbm_controller_tb_simple__Syms* const vlSymsp;

    // CONSTRUCTORS
    Vhbm_controller_tb_simple___024root(Vhbm_controller_tb_simple__Syms* symsp, const char* v__name);
    ~Vhbm_controller_tb_simple___024root();
    VL_UNCOPYABLE(Vhbm_controller_tb_simple___024root);

    // INTERNAL METHODS
    void __Vconfigure(bool first);
};


#endif  // guard
