'''
Constants file
'''


class abstractdomains:
    polyhedra = "polyhedra"
    interval = "interval"
    octagon = "octagon"


class threshold:
    none = "none"
    mergeall = "all_in"
    user = "user"
    head = "project_head"
    head_var = "project_head_var"
    call = "project_call"
    call_var = "project_call_var"


class cfr:
    class properties:
        general = "cfr_properties"
        split = "cfr_split_properties"
        cone = "cfr_cone_properties"
        project = "cfr_project_properties"
        rfs = "cfr_rfs_properties"
        auto = "cfr_auto_properties"
        user = "cfr_user_properties"
        head = "cfr_head_properties"
        head_var = "cfr_head_var_properties"
        call = "cfr_call_properties"
        call_var = "cfr_call_var_properties"
        john = "cfr_head_deep_properties"


class config:
    verbosity = "verbosity"
    version = "version"
    output_dir = "output_destination"
    output_formats = "output_formats"
    print_invariants = "show_with_invariants"
    tmp_dir = "tmpdir"
    ei_output = "ei_out"
    print_graphs = "print_graphs"
    different_templates = "different_template"
    different_templates_scheme = "different_template_scheme"
    scc_depth = "scc_depth"
    do_user_reachability = "user_reachability"
    reachability_absdomain = "reachability"
    remove_unused_variables = "remove_no_important_variables"
    do_check_assertions = "check_assertions"
    do_print_graph_rfs_cfr = "rfs_as_cfr_props"
    print_unknown_as_prolog = "print_scc_prolog"
    files = "files"
    nt_algs = "nontermination"
    t_algs = "termination"
    do_conditional_termination = "conditional_termination"
    fast_answer = "stop_if_fail"

    class invariants:
        absdomain = "invariants"
        user_widenning_nodes = "invariant_widening_nodes"
        widenning_frequency = ""
        widenning_nodes_mode = "invariant_widening_nodes_mode"
        threshold_mode = "invariants_threshold"

    class cfr:
        iterations = "cfr_iterations"
        max_tries = "cfr_max_tries"
        strategy_before = "cfr_strategy_before"
        strategy_scc = "cfr_strategy_scc"
        strategy_after = "cfr_strategy_after"
        inner_invariants = "cfr_invariants"
        user_nodes = "cfr_nodes"
        nodes_mode = "cfr_nodes_mode"

        class properties:
            user = "cfr_user_properties"
            cone = "cfr_cone_properties"
            head = "cfr_head_properties"
            head_var = "cfr_head_var_properties"
            call = "cfr_call_properties"
            call_var = "cfr_call_var_properties"
            john = "cfr_head_deep_properties"
            split = "cfr_split_properties"
