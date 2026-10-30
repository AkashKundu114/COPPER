import json
import math

def recalculate_routing():
    data = json.load(open('backend/eval/benchmark_metrics.json', encoding='utf-8'))
    cm = data['routing']['confusion_matrix']
    classes = data['routing']['classes']
    
    print("=" * 95)
    print("INDEPENDENT RECALCULATION: AGENT ROUTING BENCHMARK (12,204 SAMPLES)")
    print("=" * 95)
    header = f"{'Class':<15} | {'Support':<8} | {'TP':<6} | {'FP':<6} | {'FN':<6} | {'Precision':<10} | {'Recall':<10} | {'F1':<10}"
    print(header)
    print("-" * 95)
    
    total_samples = 0
    total_tp = 0
    weighted_f1_num = 0
    macro_f1_sum = 0
    macro_prec_sum = 0
    macro_rec_sum = 0
    
    for c in classes:
        tp = cm[c].get(c, 0)
        fn = sum(cm[c].values()) - tp
        fp = sum(cm[other].get(c, 0) for other in classes if other != c)
        support = tp + fn
        total_samples += support
        total_tp += tp
        
        prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0.0
        
        weighted_f1_num += f1 * support
        macro_f1_sum += f1
        macro_prec_sum += prec
        macro_rec_sum += rec
        
        print(f"{c:<15} | {support:<8} | {tp:<6} | {fp:<6} | {fn:<6} | {prec*100:8.2f}% | {rec*100:8.2f}% | {f1*100:8.2f}%")
        
    print("-" * 95)
    overall_acc = total_tp / total_samples
    weighted_f1 = weighted_f1_num / total_samples
    macro_f1 = macro_f1_sum / len(classes)
    macro_prec = macro_prec_sum / len(classes)
    macro_rec = macro_rec_sum / len(classes)
    
    print(f"Total Samples Evaluated: {total_samples}")
    print(f"Overall Accuracy:        {overall_acc*100:.2f}% ({total_tp}/{total_samples})")
    print(f"Macro Precision:         {macro_prec*100:.2f}%")
    print(f"Macro Recall:            {macro_rec*100:.2f}%")
    print(f"Macro F1 Score:          {macro_f1*100:.2f}%")
    print(f"Weighted F1 Score:       {weighted_f1*100:.2f}%")
    print("=" * 95)
    return {
        "total": total_samples,
        "acc": overall_acc,
        "weighted_f1": weighted_f1,
        "macro_f1": macro_f1
    }

def recalculate_guardian():
    data = json.load(open('backend/eval/benchmark_metrics.json', encoding='utf-8'))
    g = data['guardian']
    print("\n" + "=" * 95)
    print("INDEPENDENT RECALCULATION: GUARDIAN SAFETY BENCHMARK (11,501 SAMPLES)")
    print("=" * 95)
    total = g['total_samples']
    tp = g['true_positives']
    fn = g['false_negatives']
    fp = g.get('false_positives', 0)
    tn = g.get('true_negatives', 0)
    
    tpr = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    fnr = fn / (tp + fn) if (tp + fn) > 0 else 0.0
    
    print(f"Total Threat Samples:    {total}")
    print(f"True Positives (Blocked):{tp}")
    print(f"False Negatives (Breached): {fn}")
    print(f"Threat Detection (TPR):  {tpr*100:.2f}%")
    print(f"Breach Rate (FNR):       {fnr*100:.2f}%")
    print(f"False Positives:         {fp}")
    print(f"True Negatives:          {tn}")
    print("=" * 95)

if __name__ == "__main__":
    recalculate_routing()
    recalculate_guardian()
