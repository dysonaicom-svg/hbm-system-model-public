// ------------------------------------------------------------
// uvm.svh - Minimal Verilator-compatible UVM stub
// ------------------------------------------------------------
package uvm_pkg;

    timeunit 1ns;
    timeprecision 1ps;

    const int UVM_NONE = 0;
    const int UVM_LOW = 100;
    const int UVM_MEDIUM = 200;
    const int UVM_HIGH = 300;
    const int UVM_FULL = 400;
    const int UVM_DEBUG = 500;
    const int UVM_ACTIVE = 1;
    const int UVM_PASSIVE = 0;

    class uvm_phase;
        string name;
        function new(string n); name = n; endfunction
    endclass

    class uvm_object;
        string name;
        function new(string n = ""); name = n; endfunction
        function string get_name(); return name; endfunction
        function string convert2string(); return name; endfunction
        function void do_copy(uvm_object rhs); endfunction
        function bit do_compare(uvm_object rhs); return 0; endfunction
    endclass

    class uvm_component extends uvm_object;
        uvm_component parent;
        uvm_phase phase;
        function new(string n, uvm_component p);
            super.new(n); parent = p;
        endfunction
        function void build_phase(uvm_phase p); endfunction
        function void connect_phase(uvm_phase p); endfunction
        function void end_of_elaboration_phase(uvm_phase p); endfunction
        function void extract_phase(uvm_phase p); endfunction
        function void run_phase(uvm_phase p); endfunction
        function void report_phase(uvm_phase p); endfunction
    endclass

    class uvm_sequence_item extends uvm_object;
        function new(string n = ""); super.new(n); endfunction
    endclass

    class uvm_sequencer extends uvm_component;
        function new(string n, uvm_component p); super.new(n, p); endfunction
    endclass

    class uvm_driver extends uvm_component;
        function new(string n, uvm_component p); super.new(n, p); endfunction
        function void run_phase(uvm_phase p); endfunction
    endclass

    class uvm_monitor extends uvm_component;
        function new(string n, uvm_component p); super.new(n, p); endfunction
    endclass

    class uvm_scoreboard extends uvm_component;
        function new(string n, uvm_component p); super.new(n, p); endfunction
    endclass

    class uvm_agent extends uvm_component;
        function new(string n, uvm_component p); super.new(n, p); endfunction
    endclass

    class uvm_env extends uvm_component;
        function new(string n, uvm_component p); super.new(n, p); endfunction
    endclass

    class uvm_test extends uvm_env;
        function new(string n, uvm_component p); super.new(n, p); endfunction
    endclass

    class uvm_analysis_port;
        function new(string n, uvm_component p); endfunction
        function void write(uvm_object o); endfunction
        function void connect(uvm_component c); endfunction
    endclass

    class uvm_config_db;
        static function bit get(uvm_component c, string inst, string field, inout uvm_object v);
            return 0;
        endfunction
        static function void set(uvm_component c, string inst, string field, uvm_object v);
        endfunction
    endclass

    class uvm_sequence extends uvm_object;
        function new(string n = ""); super.new(n); endfunction
        function void body(); endfunction
    endclass

    `define uvm_object_utils(T)
    `define uvm_component_utils(T)
    `define uvm_field_utils(T)
    `define uvm_info(ID, MSG, VERB) $display("[INFO] %s: %s", ID, MSG);
    `define uvm_warning(ID, MSG) $display("[WARN] %s: %s", ID, MSG);
    `define uvm_error(ID, MSG) $display("[ERROR] %s: %s", ID, MSG);
    `define uvm_fatal(ID, MSG) $display("[FATAL] %s: %s", ID, MSG);

    function void run_test(string n = "");
        $display("Running test: %s", n);
    endfunction

    function void raise_objection(uvm_component c, string d);
        $display("[UVM] Objection raised: %s", d);
    endfunction
    function void drop_objection(uvm_component c, string d);
        $display("[UVM] Objection dropped: %s", d);
    endfunction

endpackage : uvm_pkg