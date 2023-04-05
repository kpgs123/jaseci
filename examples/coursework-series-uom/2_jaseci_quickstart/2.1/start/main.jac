import {*} with "./graph.jac";

walker create_family_tree {
    root{
        family_tree = spawn here ++> graph::family_tree;
        take -->;
    }
    family_root {
        father = spawn here ++> node::person(
            id = "6743482333V",
            name = "John",
            date_of_birth = "1967-01-01",
            profession = "Engineer",
            gender = "Male"
        );
        mother = spawn here ++> node::person(
            id = "694343433V",
            name = "Mary",
            date_of_birth = "1969-01-01",
            profession = "Architecture",
            gender = "Female"
        );
        son = spawn here ++> node::person(
            id = "9643482333V",
            name = "George",
            date_of_birth = "1996-01-01",
            profession = "Student",
            gender = "Male"
        );
        father <+[married]+> mother;
        son + [child] +> father;
        son + [child] +> mother;
    }
}