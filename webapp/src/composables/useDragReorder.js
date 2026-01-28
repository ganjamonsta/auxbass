/**
 * Drag & Drop reorder composable
 * Handles drag and drop reordering of lists
 */
import { ref } from 'vue'

export function useDragReorder(onReorder) {
  const dragIndex = ref(null)
  const dragOverIndex = ref(null)

  const handleDragStart = (event, index) => {
    dragIndex.value = index
    event.dataTransfer.effectAllowed = 'move'
    event.dataTransfer.setData('text/plain', index.toString())
  }

  const handleDragEnd = () => {
    dragIndex.value = null
    dragOverIndex.value = null
  }

  const handleDragOver = (event, index) => {
    event.preventDefault()
    dragOverIndex.value = index
  }

  const handleDrop = async (event, toIndex, items) => {
    event.preventDefault()
    const fromIndex = dragIndex.value

    if (fromIndex === null || fromIndex === toIndex) {
      handleDragEnd()
      return null
    }

    // Reorder items
    const reordered = [...items]
    const [movedItem] = reordered.splice(fromIndex, 1)
    reordered.splice(toIndex, 0, movedItem)

    handleDragEnd()

    // Call callback if provided
    if (onReorder) {
      await onReorder(reordered, fromIndex, toIndex)
    }

    return reordered
  }

  return {
    dragIndex,
    dragOverIndex,
    handleDragStart,
    handleDragEnd,
    handleDragOver,
    handleDrop
  }
}
